Notes about the API, made as we go

currentuser vs useras

The currentuser is the user the session authentication token uses. There are authtokens which a third party may useto masquerade as the user.
The useras is the user the method runs as. For example creating a user, group, or app, should run as the system user.

There are 3 use cases
(a) user (even as group or app owner) comes in with cookie through web interface
(b) user (even as group or app owner) comes in through a web service
(c) user comes in through a system script.

The third is the simplest case as both currentuser and system user are set through the script interface to adsgut.
For the remaining two ths currentuser is set through the cookie (or equivalent) in the web api, and comes into the function.

(Is useras needed?)

in genereal currentuser masquerades as useras where funcs take a useras@app.route('/all')


The flow:

(a) user created item. If item already exists in system, we return that instead
(b) user posts item in the saving process into his personal group
(c) use tags item. In the process the tag is posted into the personal group. The tag table
	gets an entry, so does the itemtag table.
(d) user posts an item into a group. Do we check to see if this item is saved. Yes. The item must be a item object. The item must have been saved by the user?
Or not? (ie in user private group) DECISION Or should when we add to another group or app, also write into personal group, for fast searching, if nothing else.
YES: we autopost if not in personal group
(e) Ditto for app
(f) User posts a tagging into a group/app. What must exist? item must, tag must, itemtagging must. They will all error out if these dont exist. The question is,
what of these must have been saved by user. There is no concept of saving itemtagging into a group.
Should there be.

API
---
created using: 
	grep route whosflask.py | grep -v '^#' | sed 's/\#/  |   /g' | sed 's/\@app.route(//g' | sed 's/)//g' | sed 's/(//g' | sort >> README.API.txt



@adsgut.route'/'
@adsgut.route'/all'
@adsgut.route'/app', methods=['POST']  |   name/description
@adsgut.route'/app/<appowner>/app:<appname>/acceptinvitation', methods=['POST']  |   accept
@adsgut.route'/app/<appowner>/app:<appname>/groups', methods=['GET', 'POST']  |   group
@adsgut.route'/app/<appowner>/app:<appname>/invitation', methods=['POST']  |   user
@adsgut.route'/app/<appowner>/app:<appname>/items', methods=['POST']  |   user/fqin
@adsgut.route'/app/<appowner>/app:<appname>/itemsandtags', methods=['POST']  |   user/name/itemtype/description/uri/tags=[[name, tagtype, description]...]
@adsgut.route'/app/<appowner>/app:<appname>/tags', methods=['POST']  |   user/fqin/fqtn
@adsgut.route'/app/<appowner>/app:<appname>/users', methods=['GET', 'POST']  |   user
@adsgut.route'/app/<username>/app:<appname>'
@adsgut.route'/app/<username>/app:<appname>/profile/html'
@adsgut.route'/app/html'
@adsgut.route'/group', methods=['POST']  |   groupname/description
@adsgut.route'/group/<groupowner>/group:<groupname>/acceptinvitation', methods=['POST']  |   accepr
@adsgut.route'/group/<groupowner>/group:<groupname>/invitation', methods=['POST']  |   user
@adsgut.route'/group/<groupowner>/group:<groupname>/items', methods=['POST']  |   user/fqin
@adsgut.route'/group/<groupowner>/group:<groupname>/itemsandtags', methods=['POST']  |   user/name/itemtype/description/uri/tags=[[name, tagtype, description]...]
@adsgut.route'/group/<groupowner>/group:<groupname>/tags', methods=['POST']  |   user/fqin/fqtn
@adsgut.route'/group/<groupowner>/group:<groupname>/users', methods=['GET', 'POST']  |   user
@adsgut.route'/group/<username>/group:<groupname>'
@adsgut.route'/group/<username>/group:<groupname>/profile/html'
@adsgut.route'/group/html'
@adsgut.route'/item/<nick>/<ns>/<itemname>'
@adsgut.route'/item/<nick>/byuri/<itemuri>'
@adsgut.route'/items'  |   q=fieldlist=['uri','', 'name','', 'itemtype','', 'context', None, 'fqin', None]
@adsgut.route'/items/<nick>', methods=['POST']  |   name/itemtype/uri/description
@adsgut.route'/items/<nick>/<tagspace>/<tagtypename>:<tagname>'  |   q=fieldlist=['uri','', 'name','', 'itemtype','', 'context', None, 'fqin', None]
@adsgut.route'/items/<nick>/byspec'  |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None, 'itemuri', '', 'itemname', '', 'itemtype', '']
@adsgut.route'/login', methods=['GET', 'POST']
@adsgut.route'/logout'
@adsgut.route'/poal'
@adsgut.route'/tags'  |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None]
@adsgut.route'/tags/<nick>/<ns>/<itemname>', methods=['GET', 'POST']  |   tagname/tagtype/description   |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None]
@adsgut.route'/tags/<nick>/byspec'  |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None, 'itemuri', '', 'itemname', '', 'itemtype', '']
@adsgut.route'/user/<nick>'
@adsgut.route'/user/<nick>/appsin'
@adsgut.route'/user/<nick>/appsinvited'
@adsgut.route'/user/<nick>/appsowned'
@adsgut.route'/user/<nick>/groupsin'
@adsgut.route'/user/<nick>/groupsinvited'
@adsgut.route'/user/<nick>/groupsowned'
@adsgut.route'/user/<nick>/items'  |   q=fieldlist=['itemtype','', 'context', None, 'fqin', None]
@adsgut.route'/user/<nick>/items/html'
@adsgut.route'/user/<nick>/profile/html'
@adsgut.route'/user/<nick>/tags'  |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None]
