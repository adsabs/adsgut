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



