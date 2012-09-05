Notes about the API, made as we go

currentuser vs useras

The currentuser is the user the session authentication token uses. This token comes from Giovanni's user
object or from oauth.

The useras is the user the method runs as. For example creating a user, group, or app, should run as the system user.

There are 3 use cases
(a) user (even as group or app owner) comes in with cookie through web interface
(b) user (even as group or app owner) comes in through a web service
(c) user comes in through a system script.

The third is the simplest case as both currentuser and system user are set through the script interface to adsgut.
For the remaining two ths currentuser is set through the cookie (or equivalent) in the web api, and comes into the function.

(Is useras needed?)

in genereal currentuser masquerades as useras where funcs take a useras@app.route('/all')


'/all'
'/'
'/poal'
'/login', methods=['GET', 'POST']
'/logout'
'/user/<nick>'
'/user/<nick>/profile/html'
'/user/<nick>/groupsin'
'/user/<nick>/groupsowned'
'/user/<nick>/groupsinvited'
'/user/<nick>/appsin'
'/user/<nick>/appsowned'
'/user/<nick>/appsinvited'
'/group', methods=['post']  |   groupname/description
'/group/<groupowner>/group:<groupname>/invitation', methods=['post']  |   user
'/groupinvite/<groupowner>/group:<groupname>', methods=['post']  |   accepr
'/group/<groupowner>/group:<groupname>/adduser', methods=['post']  |   user
'/app', methods=['post']  |   name/description
'/app/<appowner>/app:<appname>/invitation', methods=['post']  |   user
'/appinvite/<appowner>/app:<appname>', methods=['post']  |   accept
'/app/<appowner>/app:<appname>/adduser', methods=['post']  |   user
'/group/html'
'/group/<username>/group:<groupname>'
'/group/<username>/group:<groupname>/profile/html'
'/group/<username>/group:<groupname>/users'
'/app/html'
'/app/<username>/app:<appname>'
'/app/<username>/app:<appname>/profile/html'
'/app/<username>/app:<appname>/users'
'/app/<username>/app:<appname>/groups'
'/item/<nick>', methods=['POST']  |   name/itemtype/uri/description
'/tag/<nick>/<ns>/<itemname>', methods=['POST']  |   tagname/tagtype/description
'/item/<ns>/<itemname>/grouppost', methods=['POST']  |   user/fqin
'/item/<ns>/<itemname>/apppost', methods=['POST']  |   user/fqin
'/tag/<ns>/<itemname>/grouppost', methods=['POST']  |   user/fqin/fqtn
'/tag/<ns>/<itemname>/apppost', methods=['POST']  |   user/fqin/fqtn
'/item/<nick>/<ns>/<itemname>'
'/itembyuri/<nick>/<itemuri>'
'/items'  |   q=fieldlist=[('uri','', ('name','', ('itemtype','', ('context', None, ('fqin', None]
'/tags'  |   q=fieldlist=[('tagname','', ('tagtype','', ('context', None, ('fqin', None]
'/item/<nick>/<ns>/<itemname>/tags'  |   fieldlist=[('tagname','', ('tagtype','', ('context', None, ('fqin', None]
'/tag/<nick>/<tagspace>/<tagtypename>:<tagname>/items'  |   q=fieldlist=[('uri','', ('name','', ('itemtype','', ('context', None, ('fqin', None]
'/itemspec/<nick>/tags'  |   fieldlist=[('tagname','', ('tagtype','', ('context', None, ('fqin', None, ('itemuri', '', ('itemname', '', ('itemtype', '']
'/tagspec/<nick>/items'  |   ieldlist=[('tagname','', ('tagtype','', ('context', None, ('fqin', None, ('itemuri', '', ('itemname', '', ('itemtype', '']
'/user/<nick>/items'  |   fieldlist=[('itemtype','', ('context', None, ('fqin', None]
'/user/<nick>/tags'  |   fieldlist=[('tagname','', ('tagtype','', ('context', None, ('fqin', None]
'/user/<nick>/items/html'
  |    '/tags/<username>/<tagtype>:<tagname>'
  |    '/tags/<tagtype>:<tagname>/'
