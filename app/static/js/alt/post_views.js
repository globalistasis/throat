/* Post-related views:
 *  - [ ] View post
 *     - [ ] View comments
 *     - [ ] Edit comments
 *     - [ ] Delete comments
 *  - [ ] Create post
 *  - [ ] Edit post
 *  - [ ] Delete post
 */

 var view_post = {
   controller: function (){
     var ctrl = this;
     ctrl.err = '';
     ctrl.sub = m.route.param('sub');
     m.startComputation();
     window.stop();  // We're going to change pages, so cancel all requests.
     m.request({
       method: 'GET',
       url: '/do/get_post/' + m.route.param('pid')
     }).then(function(res) {
         if (res.status == 'ok'){
           ctrl.post = res.post;
         } else {
           ctrl.err = res.error;
         }
         m.endComputation();
     }).catch(function(err) {
       ctrl.err = [err];
       m.endComputation();
     });
   },
   view: function(ctrl) {
     if (ctrl.err !== ''){
       return m('div.content.pure-u-1', {}, "Error loading post: " + ctrl.err);
     }else {
       if (!ctrl.post) {
         return [m('div.content.pure-u-1 pure-u-md-18-24', {}, 'Loading...'),
                 m('div.sidebar.pure-u-1 pure-u-md-6-24')];
       } else {
         var post = ctrl.post;
         return [m('div.content.pure-u-1 pure-u-md-18-24', {},
                  m('article.post.center',
                    m('div.head',
                      (post.nsfw) ? m('div.bgred', {title: 'Not safe for work'}, 'NSFW') : '',
                      (post.thumbnail) ? m('div.thpostcontainer', m('div.thumbnail', decide_thumb(post))) : '',
                      m('h1.title',
                        m('a', (post.ptype === 0) ? {href: '/s/' + ctrl.sub + '/' + post.pid, config: m.route} : {href: post.link}, post.title)
                      ), m('div.info', 'posted by ',
                        function () {
                          switch (post.deleted){
                            case 0:
                              return m('a', {href: '/u/' + post.user, config: m.route}, post.user);
                            case 1:
                              return '[Deleted by user]';
                            case 2:
                              return '[Deleted]';
                          }
                        }()
                        /* TODO: Save, edit, delete and flair buttons */
                      ),
                      (post.ptype === 0) ? m('div.content', m.trust(md.makeHtml(post.content))) : ''
                    )
                  )
                ),
                 m('div.sidebar.pure-u-1 pure-u-md-6-24')];
       }
     }
   }
 };
