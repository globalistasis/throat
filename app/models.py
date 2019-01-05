""" Database and storage related functions and classes """
import datetime
import redis
from flask import g
from peewee import IntegerField, DateTimeField, BooleanField, Proxy, Model
from peewee import CharField, ForeignKeyField, TextField, PrimaryKeyField
from playhouse.db_url import connect as db_url_connect
import config

# Why not here? >_>
rconn = redis.from_url(config.SOCKETIO_REDIS_URL)

dbm = db_url_connect(config.DATABASE_URL, charset='utf8mb4')
dex = dbm.execute


def peewee_count_queries(*args, **kwargs):
    """ Used to count and display number of queries """
    if not hasattr(g, 'pqc'):
        g.pqc = 0
    g.pqc += 1
    return dex(*args, **kwargs)


dbm.execute = peewee_count_queries


db = Proxy()
db.initialize(dbm)


class TModel(Model):
    class Meta:
        database = db


class User(TModel):
    uid = CharField(primary_key=True, max_length=40)
    crypto = IntegerField()  # Password hash algo, 1 = bcrypt.
    email = CharField(null=True)
    joindate = DateTimeField(null=True)
    name = CharField(null=True, unique=True, max_length=64)
    password = CharField(null=True)

    score = IntegerField(default=0)  # AKA phuks taken
    given = IntegerField(default=0)  # AKA phuks given
    # status: 0 = OK; 10 = deleted
    status = IntegerField(default=0)
    resets = IntegerField(default=0)

    class Meta:
        table_name = 'user'


class Client(TModel):
    _default_scopes = TextField(null=True)
    _redirect_uris = TextField(null=True)
    client = CharField(db_column='client_id', primary_key=True, max_length=40)
    client_secret = CharField(unique=True, max_length=55)
    is_confidential = BooleanField(null=True)
    name = CharField(null=True, max_length=40)
    user = ForeignKeyField(db_column='user_id', null=True, model=User, field='uid')

    class Meta:
        table_name = 'client'


class Grant(TModel):
    _scopes = TextField(null=True)
    client = ForeignKeyField(db_column='client_id', model=Client, field='client')
    code = CharField(index=True)
    expires = DateTimeField(null=True)
    redirect_uri = CharField(null=True)
    user = ForeignKeyField(db_column='user_id', null=True, model=User,
                           field='uid')

    class Meta:
        table_name = 'grant'


class Message(TModel):
    content = TextField(null=True)
    mid = PrimaryKeyField()
    mlink = CharField(null=True)
    # mtype values: 
    # 1: sent, 4: post replies, 5: comment replies, 8: mentions, 9: saved message
    # 6: deleted, 41: ignored messages  => won't display anywhere
    # 2 (mod invite), 7 (ban notification), 11 (deletion): modmail
    mtype = IntegerField(null=True)
    posted = DateTimeField(null=True)
    read = DateTimeField(null=True)
    receivedby = ForeignKeyField(db_column='receivedby', null=True,
                                 model=User, field='uid')
    sentby = ForeignKeyField(db_column='sentby', null=True, model=User,
                             backref='user_sentby_set', field='uid')
    subject = CharField(null=True)

    class Meta:
        table_name = 'message'


class SiteLog(TModel):
    action = IntegerField(null=True)
    desc = CharField(null=True)
    lid = PrimaryKeyField()
    link = CharField(null=True)
    time = DateTimeField(default=datetime.datetime.utcnow())

    class Meta:
        table_name = 'site_log'


class SiteMetadata(TModel):
    key = CharField(null=True)
    value = CharField(null=True)
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'site_metadata'


class Sub(TModel):
    name = CharField(null=True, unique=True, max_length=32)
    nsfw = BooleanField(default=False)
    sid = CharField(primary_key=True, max_length=40)
    sidebar = TextField(default='')
    status = IntegerField(null=True)
    title = CharField(null=True, max_length=50)
    sort = CharField(null=True, max_length=32)
    creation = DateTimeField(default=datetime.datetime.utcnow)
    subscribers = IntegerField(default=1)
    posts = IntegerField(default=0)

    class Meta:
        table_name = 'sub'


class SubFlair(TModel):
    sid = ForeignKeyField(db_column='sid', null=True, model=Sub,
                          field='sid')
    text = CharField(null=True)
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_flair'


class SubLog(TModel):
    action = IntegerField(null=True)
    desc = CharField(null=True)
    lid = PrimaryKeyField()
    link = CharField(null=True)
    sid = ForeignKeyField(db_column='sid', null=True, model=Sub,
                          field='sid')
    time = DateTimeField(default=datetime.datetime.utcnow())

    class Meta:
        table_name = 'sub_log'


class SubMetadata(TModel):
    key = CharField(null=True)
    sid = ForeignKeyField(db_column='sid', null=True, model=Sub,
                          field='sid')
    value = CharField(null=True)
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_metadata'


class SubPost(TModel):
    content = TextField(null=True)
    deleted = IntegerField(null=True)
    link = CharField(null=True)
    nsfw = BooleanField(null=True)
    pid = PrimaryKeyField()
    posted = DateTimeField(null=True)
    edited = DateTimeField(null=True)
    ptype = IntegerField(null=True) # 1=text, 2=link, 3=poll
    score = IntegerField(null=True)
    sid = ForeignKeyField(db_column='sid', null=True, model=Sub, field='sid')
    thumbnail = CharField(null=True)
    title = CharField(null=True)
    comments = IntegerField()
    uid = ForeignKeyField(db_column='uid', null=True, model=User, field='uid')
    flair = CharField(null=True, max_length=25)

    class Meta:
        table_name = 'sub_post'


class SubPostPollOption(TModel):
    """ List of options for a poll """
    pid = ForeignKeyField(db_column='pid', model=SubPost, field='pid')
    text = CharField()

    class Meta:
        table_name = 'sub_post_poll_option'


class SubPostPollVote(TModel):
    """ List of options for a poll """ 
    pid = ForeignKeyField(db_column='pid', model=SubPost, field='pid')
    uid = ForeignKeyField(db_column='uid', model=User)
    vid = ForeignKeyField(db_column='vid', model=SubPostPollOption, backref='votes')

    class Meta:
        table_name = 'sub_post_poll_vote'


class SubPostComment(TModel):
    cid = CharField(primary_key=True, max_length=40)
    content = TextField(null=True)
    lastedit = DateTimeField(null=True)
    parentcid = ForeignKeyField(db_column='parentcid', null=True,
                                model='self', field='cid')
    pid = ForeignKeyField(db_column='pid', null=True, model=SubPost,
                          field='pid')
    score = IntegerField(null=True)
    status = IntegerField(null=True)
    time = DateTimeField(null=True)
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')

    class Meta:
        table_name = 'sub_post_comment'


class SubPostCommentVote(TModel):
    datetime = DateTimeField(null=True)
    cid = CharField(null=True)
    positive = IntegerField(null=True)
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_post_comment_vote'


class SubPostMetadata(TModel):
    key = CharField(null=True)
    pid = ForeignKeyField(db_column='pid', null=True, model=SubPost,
                          field='pid')
    value = CharField(null=True)
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_post_metadata'


class SubPostVote(TModel):
    datetime = DateTimeField(null=True)
    pid = ForeignKeyField(db_column='pid', null=True, model=SubPost,
                          field='pid')
    positive = IntegerField(null=True)
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_post_vote'


class SubStylesheet(TModel):
    content = TextField(null=True)
    source = TextField()
    sid = ForeignKeyField(db_column='sid', null=True, model=Sub,
                          field='sid')
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_stylesheet'


class SubSubscriber(TModel):
    """ Stores subscribed and blocked subs """
    order = IntegerField(null=True)
    sid = ForeignKeyField(db_column='sid', null=True, model=Sub, field='sid')
    # status is 1 for subscribed, 2 for blocked and 4 for saved (displayed in the top bar)
    status = IntegerField(null=True)
    time = DateTimeField(default=datetime.datetime.utcnow())
    uid = ForeignKeyField(db_column='uid', null=True, model=User, field='uid')
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'sub_subscriber'


class Token(TModel):
    _scopes = TextField(null=True)
    access_token = CharField(null=True, unique=True, max_length=100)
    client = ForeignKeyField(db_column='client_id', model=Client,
                             field='client')
    expires = DateTimeField(null=True)
    refresh_token = CharField(null=True, unique=True, max_length=100)
    token_type = CharField(null=True, max_length=40)
    user = ForeignKeyField(db_column='user_id', null=True, model=User,
                           field='uid')

    class Meta:
        table_name = 'token'


class UserBadge(TModel):
    badge = CharField(null=True)
    bid = CharField(primary_key=True, max_length=40)
    name = CharField(null=True, max_length=40)
    text = CharField(null=True)
    value = IntegerField(null=True)

    class Meta:
        table_name = 'user_badge'


class UserMetadata(TModel):
    key = CharField(null=True)
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')
    value = CharField(null=True)
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'user_metadata'


class UserSaved(TModel):
    pid = IntegerField(null=True)
    uid = CharField(null=True)
    xid = PrimaryKeyField()

    class Meta:
        table_name = 'user_saved'


class Pixel(TModel):
    xid = PrimaryKeyField()
    posx = IntegerField()
    posy = IntegerField()
    value = IntegerField()
    color = IntegerField()
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')

    class Meta:
        table_name = 'pixel'


class Shekels(TModel):
    xid = PrimaryKeyField()
    shekels = IntegerField()
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')

    class Meta:
        table_name = 'shekels'


class UserUploads(TModel):
    xid = PrimaryKeyField()
    pid = ForeignKeyField(db_column='pid', null=True, model=SubPost,
                          field='pid')
    uid = ForeignKeyField(db_column='uid', null=True, model=User,
                          field='uid')
    fileid = CharField(null=True)
    thumbnail = CharField(null=True)
    status = IntegerField()

    class Meta:
        table_name = 'user_uploads'


class SubUploads(TModel):
    sid = ForeignKeyField(db_column='sid', model=Sub, field='sid')
    fileid = CharField()
    thumbnail = CharField()
    name = CharField()
    size = IntegerField()

    class Meta:
        table_name = 'sub_uploads'


class UserIgnores(TModel):
    uid = ForeignKeyField(db_column='uid', model=User,
                          field='uid')
    target = CharField(max_length=40)
    date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = 'user_ignores'
