from dbase import setup_db
import whos, posts
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, escape, make_response, jsonify, Blueprint
import sys, os
import hashlib
from permissions import permit
from errors import abort
engine, db_session=setup_db("/tmp/adsgut.db")


from functools import wraps
def makejson():
    def decorator(f):
        @wraps(f)
        def decorated_func(*args,**kwargs):
            retdict=f(*args, **kwargs)
            return jsonify(**retdict)
        return decorated_func
    return decorator

#sys.path.append('..')
BLUEPRINT_MODE=os.environ.get('BLUEPRINT_MODE', False)
BLUEPRINT_MODE=bool(BLUEPRINT_MODE)
if BLUEPRINT_MODE==True:
    print "IN BLUEPRINT MODE"
    adsgut = Blueprint('adsgut', __name__)
else:
    adsgut=Flask(__name__)
    adsgut.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


def formwithdefaults(specdict, spec, request):
    for k in spec.keys():
        specdict[k]=request.form.get(spec[k][0], spec[k][1])

#######################################################################################################################
#session.authtoken is a set of privileges the user has granted the application based on an oauth or other mechanism (such as an API key)
#currently we dont provide it so we cant have third party groups and users masquerade. Its not necessary for Jan, but is needed
#for oauth and other things and can be used to support API users.

@adsgut.before_request
def before_request():
        #print "BEFORE REQUEST", session
        #g.db=whos.Whosdb(db_session)
        g.dbp=posts.Postdb(db_session)
        g.db=g.dbp.whosdb
        if session.has_key('username'):
            g.currentuser=g.db.getUserForNick(None, session['username'])
        else:
            g.currentuser=None
        if session.has_key('authtoken'):
            g.authtoken=session['authtoken']
        else:
            g.authtoken=None

@adsgut.teardown_request
def shutdown_session(exception=None):
    g.db.commit()
    g.dbp.commit()
    print "COMMITTED====="
    g.db.remove()
    g.dbp.remove()

#EXPLICITLY COMMIT ON POSTS. THOUGH TO DO MULTIPLE THINGS, WE MAY WANT TO 
#SCHEDULE COMMITS SEPARATELY..really commits not a property of whosdb
#currently explicit for simplicity

#######################################################################################################################
#The methods here are to support Poal and other testing infrastructure.

@adsgut.route('/all')
def indexall():
    return render_template('allindex.html', users=g.db.allUsers(g.currentuser), 
        groups=g.db.allGroups(g.currentuser), apps=g.db.allApps(g.currentuser))

@adsgut.route('/')
def index():
    return render_template('index.html', suppressed=True, poal=True)

#######################################################################################################################
@adsgut.route('/poal')
def poal():
    return render_template('poal.html', poal=True)

#######################################################################################################################
#TODO: redo this with new user system

@adsgut.route('/login', methods=['GET', 'POST'])
def login():
    error=None
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['logged_in'] = True
        flash('You were logged in')
        return redirect(url_for('index'))
    return render_template('login.html', error=error)

@adsgut.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

#######################################################################################################################
#######################################################################################################################

#Information about users, groups, and apps
#TODO: should we support a modicum of user information for others
#like group and app owners?
@adsgut.route('/user/<nick>')
def userInfo(nick):
    useras=self.getUserForNick(currentuser, nick)
    userinfo=g.db.getUserInfo(g.currentuser, useras)
    return jsonify(userinfo)

@adsgut.route('/user/<nick>/profile/html')
def userProfileHtml(nick):
    useras=self.getUserForNick(currentuser, nick)
    userinfo=g.db.getUserInfo(g.currentuser, useras)
    return render_template('userprofile.html', theuser=userinfo)

@adsgut.route('/user/<nick>/groupsuserisin')
def groupsUserIsIn(nick):
    useras=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.groupsForUser(g.currentuser, useras)
    groupdict={'groups':groups}
    return jsonify(groupdict)

@adsgut.route('/user/<nick>/groupsuserowns')
def groupsUserOwns(nick):
    useras=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.ownerOfGroups(g.currentuser, useras)
    groupdict={'groups':groups}
    return jsonify(groupdict)

@adsgut.route('/user/<nick>/groupsuserisinvitedto')
def groupsUserIsInvitedTo(nick):
    useras=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.groupInvitationsForUser(g.currentuser, useras)
    groupdict={'groups':groups}
    return jsonify(groupdict)

@adsgut.route('/user/<nick>/appsuserisin')
def appsUserIsIn(nick):
    useras=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.appsForUser(g.currentuser, useras)
    appdict={'apps':apps}
    return jsonify(appdict)

@adsgut.route('/user/<nick>/appsuserowns')
def appsUserOwns(nick):
    useras=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.ownerOfApps(g.currentuser, useras)
    appdict={'apps':apps}
    return jsonify(appdict)

#use this for the email invitation?
@adsgut.route('/user/<nick>/appsuserisinvitedto')
def appsUserIsInvitedTo(nick):
    useras=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.appInvitationsForUser(g.currentuser, useras)
    appdict={'apps':apps}
    return jsonify(appdict)

#######################################################################################################################
#creating groups and apps
#accepting invites.
#DELETION methods not there BUG

@adsgut.route('/group', methods=['POST'])#groupname/description
def createGroup():
    user=g.currentuser
    groupspec={}
    if request.method == 'POST':
        groupname=request.form.get('name', None)
        if not groupname:
            doabort("BAD_REQ", "No Group Specified")
        description=request.form.get('description', '')
        groupspec['creator']=user
        groupspec['name']=groupname
        groupspec['description']=description
        newgroup=g.db.addGroup(g.currentuser, user, groupspec)
        g.db.commit()
        return jsonify({'status':'OK', 'info': newgroup.info()})
    else:
        doabort("BAD_REQ", "GET not supported")

#Currently wont allow you to create app, or accept invites to apps
#TODO: perhaps combine these two into one invitation as a restian endpoint with action=invite or accept. 
#This way both currentuser and useras can be supported in here.
@adsgut.route('/group/<groupowner>/group:<groupname>/invitation', methods=['POST'])#user
def makeInviteToGroup(groupowner, groupname):
    #add permit to match user with groupowner
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        nick=request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "No User Specified")
        usertobeadded=g.db.getUserForNick(g.currentuser, nick)
        g.db.inviteUserToGroup(g.currentuser, fqgn, usertobeadded, None)
        g.db.commit()
        return jsonify({'status':'OK', 'info': {'invited':nick, 'to':fqgn}})
    else:
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/group/<groupowner>/group:<groupname>/acceptinvitation', methods=['POST'])#accepr
def acceptInviteToGroup(nick, groupowner, groupname):  
    userinvited=g.currentuser
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        accept=request.form.get('accept', 'NA')
        if accept==True:
            g.db.acceptInviteToGroup(g.currentuser, fqgn, userinvited, None)
            g.db.commit()
            return jsonify({'status':'OK', 'info': {'invited':nick, 'to': fqgn, 'accepted':True}})
        elif accept==False:
            return jsonify({'status': 'OK', 'info': {'invited':nick, 'to': fqgn, 'accepted':False}})
        else:
            doabort("BAD_REQ", "accept not provided")
    else:
        doabort("BAD_REQ", "GET not supported")

#This is used for addition of a user. Whats the usecase? current perms protect this
#TODO: maybe add a bulk version? That would seem to need to be added as a pythonic API: also split there into two things in pythonic API?
#BUG: user leakage as we do user info for all users in group. another users groups should not be obtainable
@adsgut.route('/group/<groupowner>/group:<groupname>/users', methods=['GET', 'POST'])#user
def addUsertoGroup_or_groupUsers(groupowner, groupname):
    #add permit to match user with groupowner
    fqgn=groupowner+"/group:"+groupname
    gowner=g.db.getUserForNick(g.currentuser, groupowner)
    if request.method == 'POST':
        permit(gowner==g.currentuser or g.db.isSystemUser(g.currentuser), "Only Group owner System User allowed")
        nick=request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "No User Specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        g.db.addUserToGroup(g.currentuser, fqgn, user, None)
        g.db.commit()
        return jsonify({'status':'OK', 'info': {'user':nick, 'group':fqgn}})
    else:
        users=g.db.usersInGroup(g.currentuser,fqgn)
        userdict={'users':users}
        return jsonify(userdict)

# @adsgut.route('/group/<username>/group:<groupname>/users')
# def group_users(username, groupname):
#     fqgn = username+'/group:'+groupname
#     users=g.db.usersInGroup(g.currentuser,fqgn)
#     return jsonify({'users':users})

@adsgut.route('/app', methods=['POST'])#name/description
def createApp():
    user=g.currentuser
    appspec={}
    if request.method == 'POST':
        appname=request.form.get('name')
        if not appname:
            doabort("BAD_REQ", "No App Specified")
        description=request.form.get('description', '')
        appspec['creator']=user
        appspec['name']=appname
        appspec['description']=description
        newapp=g.db.addApp(g.currentuser, user, appspec)
        g.db.commit()
        return jsonify({'status':'OK', 'info':newapp.info()})
    else:
        doabort("BAD_REQ", "GET not supported")

#Currently wont allow you to create app, or accept invites to apps
#TODO: combine below two?, add choices for currentuser, useras.
@adsgut.route('/app/<appowner>/app:<appname>/invitation', methods=['POST'])#user
def makeInviteToApp(appowner, appname):
    #add permit to match user with groupowner
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        nick=request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "No User Specified")
        usertobeadded=g.db.getUserForNick(g.currentuser, nick)
        g.db.inviteUserToApp(g.currentuser, fqan, usertobeadded, None)
        g.db.commit()
        return jsonify({'status':'OK',  'info': {'invited':nick, 'to': fqan}})
    else:
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/app/<appowner>/app:<appname>/acceptinvitation', methods=['POST'])#accept
def acceptInviteToApp(nick, appowner, appname):  
    userinvited=g.currentuser
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        accept=request.form.get('accept', 'NA')
        if accept==True:
            g.db.acceptInviteToApp(g.currentuser, fqan, userinvited, None)
            g.db.commit()
            return jsonify({'status':'OK','info': {'invited':nick, 'to': fqan, 'accepted':True}})
        elif accept==False:
            return jsonify({'status': 'OK', 'info': {'invited':nick, 'to': fqan, 'accepted':False}})
        else:
            doabort("BAD_REQ", "accept not provided")
    else:
        doabort("BAD_REQ", "GET not supported")

#Whats the use case for this? bulk app adds which dont go through invites.
#BUG: user leakage, also, should the pythonic api part be split up into two separates?
@adsgut.route('/app/<appowner>/app:<appname>/users', methods=['GET', 'POST'])#user
def addUserToApp_or_appUsers(appowner, appname):
    #add permit to match user with groupowner
    fqan=appowner+"/app:"+appname
    aowner=g.db.getUserForNick(g.currentuser, appowner)
    if request.method == 'POST':
        permit(aowner==g.currentuser or g.db.isSystemUser(g.currentuser), "Only App owner System User allowed")
        nick=request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "No User Specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        g.db.addUserToApp(g.currentuser, fqan, user, None)
        g.db.commit()
        return jsonify({'status':'OK', 'info': {'user':nick, 'app':fqan}})
    else:
        users=g.db.usersInApp(g.currentuser,fqan)
        userdict={'users':users}
        return jsonify(userdict) 


#BUG: UNCHECKED AS WE are not systemuser or adsuser.
#TODO: split for pythonic API
@adsgut.route('/app/<appowner>/app:<appname>/groups', methods=['GET', 'POST'])#group
def addGroupToApp_or_appGroups(appowner, appname):
    #add permit to match user with groupowner
    fqan=appowner+"/app:"+appname
    aowner=g.db.getUserForNick(g.currentuser, appowner)
    if request.method == 'POST':
        permit(aowner==g.currentuser or g.db.isSystemUser(g.currentuser), "Only App owner System User allowed")
        fqgn=request.form.get('group', None)
        if not fqgn:
            doabort("BAD_REQ", "No Group Specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        grpadded=g.db.addGroupToApp(g.currentuser, fqan, fqgn, None)
        g.db.commit()
        return jsonify({'status':'OK', 'info':{'group':fqgn, 'app': fqan}})
    else:
        groups=g.db.groupsInApp(g.currentuser,fqan)
        groupdict={'groups':groups}
        return jsonify(groupdict)  
#######################################################################################################################

#POST/GET
@adsgut.route('/group/html')
def creategrouphtml():
    pass

#get group info
@adsgut.route('/group/<username>/group:<groupname>')
def groupInfo(username, groupname):
    fqgn = username+'/group:'+groupname
    groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
    return jsonify(groupinfo)

@adsgut.route('/group/<username>/group:<groupname>/profile/html')
def groupProfileHtml(username, groupname):
    fqgn = username+'/group:'+groupname
    groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
    return render_template('groupprofile.html', thegroup=groupinfo)

# @adsgut.route('/group/<username>/group:<groupname>/users')
# def group_users(username, groupname):
#     fqgn = username+'/group:'+groupname
#     users=g.db.usersInGroup(g.currentuser,fqgn)
#     return jsonify({'users':users})


#TODO: do one for a groups apps

#######################################################################################################################
#######################################################################################################################

#POST/GET
@adsgut.route('/app/html')
def createapphtml():
    pass

@adsgut.route('/app/<username>/app:<appname>')
def appInfo(username, appname):
    fqan = username+'/app:'+appname
    appinfo=g.db.getAppInfo(g.currentuser, fqan)
    return jsonify(appinfo)

@adsgut.route('/app/<username>/app:<appname>/profile/html')
def appProfileHtml(username, appname):
    fqan = username+'/app:'+appname
    appinfo=g.db.getAppInfo(g.currentuser, fqan)
    return render_template('appprofile.html', theapp=appinfo)

# @adsgut.route('/app/<username>/app:<appname>/users')
# def application_users(username, appname):
#     fqan = username+'/app:'+appname
#     users=g.db.usersInApp(g.currentuser,fqan)
#     return jsonify({'users':users})


# @adsgut.route('/app/<username>/app:<appname>/groups')
# def application_groups(username, appname):
#     fqan = username+'/app:'+appname
#     groups=g.db.groupsInApp(g.currentuser,fqan)
#     return jsonify({'groups':groups})


#######################################################################################################################
#Can a group or app post an item for a user? The answer is yes, but the implementation is complex. This is as it must post
#items to apps and groups too. So the question is: where do we develop this functionality



#POST tag
#masqueradable BUT WE DONT SUPPORT IT FOR NOW
#BUG: getting rid of nick makes the currentuser permitting complex..or does it?
#we HAVE REMOVED THE ABILITY TO POST A SINGLE TAG. YOU MUST NOW USE THE ARRAY MODEL FOR POSTING, AND USE USERTHER FOR PEOPLE
@adsgut.route('/tags/<ns>/<itemname>', methods=['GET', 'POST'])#taginfos=[{tagname/tagtype/description}] #q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
def tagsForItem(ns, itemname):
    #user=g.db.getUserForNick(g.currentuser, nick)
    tagmode=True
    nsuser=g.db.getUserForNick(g.currentuser, ns)
    #print "hello", user.nick
    if request.method == 'POST':
        #print request.form
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        #print "aaa", itspec#
        iteminfo=g.dbp.getItemByFqin(g.currentuser, nsuser.nick+"/"+itemname)
        taginfos=request.form.get('taginfos', [])
        newtaggings=[]
        for ti in taginfos:
            if not ti['tagname']:
                doabort('BAD_REQ', "No names specified for tag")
            if not ti['tagtype']:
                doabort('BAD_REQ', "No tagtypes specified for tag")
            tagspec={}
            tagspec['creator']=useras
            tagspec['name'] = ti['tagname']           
            tagspec['tagtype'] = ti['tagtype']       
            if ti.has_key('description'):
                tagspec['description']=ti['description']
            newtag, newtagging=g.dbp.tagItem(g.currentuser, useras, iteminfo['fqin'], tagspec, tagmode)
            newtaggings.append[newtagging]
        #print "kkk"
        g.dbp.commit()
        #returning the taggings requires a commit at this point
        taggings={'status':'OK', 'info':{'item': iteminfo['fqin'], 'tagging':[nt.info() for nt in newtaggings]}}
        return jsonify(taggings)
    else:
        criteria, fvlist, orderer=_getTagQuery(request.args)
        context=criteria.pop('context')
        fqin=criteria.pop('fqin')
        if criteria.get('userthere')==True:
            nick=criteria.pop('nick')
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            nick=None
            useras=g.currentuser
        taggings=g.dbp.getTagsForItem(g.currentuser, useras, ns+"/"+itemname, context, fqin, criteria)
        return jsonify(taggings)
#######################################################################################################################
#Post to group and post to app. We are nor supporting any deletion web services as yet.
#Also post tag to group and post tag to app. tag too must be saved and lookupable
#TODO: we must solve the whose items u can post problem as posting currently (for saving, atleast seems to use
#the current user)


#@adsgut.route('/item/<ns>/<itemname>/grouppost', methods=['POST'])#user/fqin
#TODOAPI: do easy way of getting items in group BUG: how about particular user via userthere?
#BUG: rahuldave masquerading as jayluker gives 0 items instead of throwing error
#BUG: userthere only does masquerading. it dosent seem to filter by user. how do we do this without a nick extension? really? i thought getItems would handle this
@adsgut.route('/group/<groupowner>/group:<groupname>/items', methods=['POST', 'GET'])#userthere/[fqins] fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None), ('userthere', 'False')]
def itemsForGroup(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqins = request.form.get('fqins', None)
        if not fqins:
            doabort("BAD_REQ", "Item to post to group not specified")
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        fqgn=groupowner+"/group:"+groupname
        items=[]
        for fqin in fqins:
            item=g.dbp.postItemIntoGroup(g.currentuser, useras, fqgn, fqin)
            items.append(item)
        g.dbp.commit()
        itempostings={'status':'OK', 'info':{'items':[item.info() for item in items], 'group':fqgn}}
        return jsonify(itempostings)
    else:
        #later support via GET all items in group, perhaps based on spec
        #doabort("BAD_REQ", "GET not supported")
        criteria, fvlist, orderer=_getItemQuery(request.args)
        #criteria['userthere']=True
        if criteria.get('userthere')==True:
            nick=criteria.pop('nick')
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            nick=None
            useras=g.currentuser
        throwawaycontext=criteria.pop('context')
        throwawayfqin=criteria.pop('fqin')
        context="group"
        fqgn=groupowner+"/group:"+groupname
        #This should be cleaned for values. BUG nor done yet.   
        items=g.dbp.getItems(g.currentuser, useras, context, fqgn, criteria, fvlist, orderer)
        grouppostings={'status':'OK', 'group':fqgn, 'items':items}
        return jsonify(grouppostings)

#TODOAPI: do easy way of getting items in group
#BUG: add userthere support (do we want to add it via GET or url?)
#this ought to allow alternate public publishing
@adsgut.route('/group/public/items', methods=['POST', 'GET'])#user/fqin fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
def useritempublicpost():
    groupowner="adsgut"
    groupname="public"
    return itemsForGroup(groupowner, groupname)

@adsgut.route('/item/<ns>/<itemname>/groups', methods=['POST'])#fqins=[fqin]
def useritemmultigrouppost(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    #user=g.db.getUserForNick(g.currentuser, nick)
    nsuser=g.db.getUserForNick(g.currentuser, ns)
    iteminfo=g.dbp.getItemByFqin(g.currentuser, nsuser.nick+"/"+itemname)
    fqin=iteminfo['fqin']
    if request.method == 'POST':
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        fqgns = request.form.get('fqins', None)
        if not fqgns:
            doabort("BAD_REQ", "groups not specified")
        for fqgn in fqgns:
            item=g.dbp.postItemIntoGroup(g.currentuser, useras, fqgn, fqin)
        g.dbp.commit()
        grouppostings={'status':'OK', 'info':{'item':item.info(), 'groups':[fqgn for fqgn in fqgns]}}
        return jsonify(grouppostings)
    else:
        #later support via GET all items in group, perhaps based on spec
        doabort("BAD_REQ", "GET not supported")

#@adsgut.route('/item/<ns>/<itemname>/apppost', methods=['POST'])#user/fqin
#TODOAPI: do easy way of getting items in group
#BUG add userthere support
@adsgut.route('/app/<appowner>/app:<appname>/items', methods=['POST'])#userthere/[fqin] fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
def useritemapppost(appowner, appname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqins = request.form.get('fqins', None)
        if not fqins:
            doabort("BAD_REQ", "Items to post to app not specified")
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        fqan=appowner+"/app:"+appname
        items=[]
        for fqin in fqins:
            item=g.dbp.postItemIntoApp(g.currentuser, useras, fqan, fqin)
            items.append(item)
        g.dbp.commit()
        itempostings={'status':'OK', 'info':{'item':[item.info() for item in items], 'app':fqan}}
        return jsonify(itempostings)
    else:
        #later support via GET all items in app, perhaps based on spec
        #doabort("BAD_REQ", "GET not supported")
        criteria, fvlist, orderer=_getItemQuery(request.args)
        #criteria['userthere']=True
        if criteria.get('userthere')==True:
            nick=criteria.pop('nick')
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            nick=None
            useras=g.currentuser
        throwawaycontext=criteria.pop('context')
        throwawayfqin=criteria.pop('fqin')
        context="app"
        fqin=appowner+"/app:"+appname
        items=g.dbp.getItems(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
        apppostings={'items':items}
        return jsonify(apppostings)


#TODO:Currently tagging into a group needs to be one by one. Change that to bulk, if it makes sense, later. Also no multiitemapp post for now
#as the default case is taken care of by 'routing'
#@adsgut.route('/tag/<ns>/<itemname>/grouppost', methods=['POST'])#user/fqin/fqtn
# should this be presented in GET?
#TODOAPI: do easy way of getting tags in grp: use spec methods

#CHECK: IN ALL OF THESE OMNIBUSEN, THE DANGER IS WE REPEAT WHAT IS BEING DOME BEFORE ROUTING AGAIN
#NEEDS OMNIPOTENCY OR CHECKS


@adsgut.route('/group/<groupowner>/group:<groupname>/tags', methods=['POST'])#userthere/fqin/fqtn
def usertaggrouppost(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        fqin = request.form.get('fqin', None)
        if not fqin:
            doabort("BAD_REQ", "item whos tags are to posted to group not specified")
        fqtn = request.form.get('fqtn', None)
        if not fqtn:
            doabort("BAD_REQ", "Tag to post to group not specified")

        it, itg=g.dbp.postTaggingIntoGroup(g.currentuser, useras, fqgn, fqin, fqtn)
        g.dbp.commit()
        taggingposted={'status':'OK', 'info': itg.info()}
        return jsonify(taggingposted)
    else:
        #doabort("BAD_REQ", "GET not supported")
        criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
        # if nick=='any':
        #     useras=g.currentuser
        # else:
        #     useras=g.db.getUserForNick(g.currentuser, nick)
        #     criteria['userthere']=True
        if criteria.get('userthere')==True:
            nick=criteria.pop('nick')
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            nick=None
            useras=g.currentuser
        throwawaycontext=criteria.pop('context')
        throwawayfqin=criteria.pop('fqin')
        context="group"
        taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqgn, criteria, fvlist, orderer)
        return jsonify(taggings)

#This posts an item, its tags, and all that to a single group
#TODOAPI: do easy way of getting tags in grp: use spec methods
#TODO: do as a multi? after all we want to add to multiple groups?

#THIS USES A FALSE TAGMODE? THIS IS THE SUPER BULK MODE. We'd use this for a siple ajax form.
@adsgut.route('/itemandtags/groups', methods=['POST'])#userthere/name/itemtype/uri/tags=[[name, tagtype, description]...]/fqgns=[fqgn]
def useritemtaggrouppost():
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    #fqgn=groupowner+"/group:"+groupname
    #grp=g.db.getGroup(g.currentuser, fqgn)
    if request.method == 'POST':
        itspec={}
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        itspec['creator']=useras
        itspec['name'] = request.form.get('name', None)
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for item")
        itspec['itemtype'] = request.form.get('itemtype', None)
        if not itspec['itemtype']:
            doabort("BAD_REQ", "No itemtype specified for item")
        #print "world"
        md5u=hashlib.md5()
        itspec['uri']=request.form.get('uri', md5u.update(useras.nick+"/"+itspec['name']))
        #itspec['description']=request.form.get('description', '')
        #itspec['uri']=request.form.get('uri', ''
        #print "aaa", itspec
        item=g.dbp.saveItem(g.currentuser, useras, itspec)
        fqgns = request.form.get('fqins', None)
        if not fqgns:
            doabort("BAD_REQ", "groups not specified")
        tagmode=False#so no tag checks
        for fqgn in fqgns:
            item=g.dbp.postItemIntoGroup(g.currentuser, useras, fqgn, fqin, tagmode)

        g.dbp.commit()
        tags=request.form.get('tags', [])#Empty array if no tags
        tagobjects=[]
        tagmode=True#so group checks while tagging.
        for tagname, tagtype, description in tags:
            tagspec={}
            tagspec['creator']=useras
            tagspec['name'] = tagname
            tagspec['tagtype'] = tagtype
            tagspec['description']=description
            tag, tagging=g.dbp.tagItem(g.currentuser, useras, item.fqin, tagspec, tagmode)
            #BELOW HANDLED BY TAGMODE=true
            # for fqgn in fqgns:
            #     it, itg=g.dbp.postTaggingIntoGroup(g.currentuser, useras, grp, item, tag)
            g.dbp.commit() # move outside to make faster
            tagobjects.append(tagging)
        itemandtaggings={'status':'OK', 'info':{'item':item.info(), 'groups': [fqgn for fqgn in fqgns], 'taggings':tagobjects}}
        return jsonify(itemandtaggings)
    else:
        doabort("BAD_REQ", "GET not supported")

#@adsgut.route('/tag/<ns>/<itemname>/apppost', methods=['POST'])#user/fqin/fqtn
#TODOAPI: do easy way of getting tags in grp: use spec methods
#TODO: change this to bulk too. What about many tags in a group?

#Unlikely to use this. whats the use case? Most of this would happen behind closed doors/
# @adsgut.route('/app/<appowner>/app:<appname>/tags', methods=['POST'])#user/fqin/fqtn
# def usertagapppost(appowner, appname):
#     #user=g.currentuser#The current user is doing the posting
#     #print "hello", user.nick
#     fqan=appowner+"/app:"+appname
#     if request.method == 'POST':
#         nick = request.form.get('userthere', None)
#         if nick:
#             useras=g.db.getUserForNick(g.currentuser, nick)
#         else:
#             useras=g.currentuser
#         fqin = request.form.get('fqin', None)
#         if not fqin:
#             doabort("BAD_REQ", "item whos tags are to posted to app not specified")
#         fqtn = request.form.get('fqtn', None)
#         if not fqtn:
#             doabort("BAD_REQ", "Tag to post to app not specified")

#         it, ita = g.dbp.postTaggingIntoApp(g.currentuser, useras, fqan, fqin, fqtn)
#         g.dbp.commit()
#         taggingposted={'status':'OK', 'info': ita.info()}
#         return jsonify(taggingposted)
#     else:
#         #doabort("BAD_REQ", "GET not supported")
#         criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
#         # if nick=='any':
#         #     useras=g.currentuser
#         # else:
#         #     useras=g.db.getUserForNick(g.currentuser, nick)
#         #     criteria['userthere']=True
#         if criteria.get('userthere')==True:
#             nick=criteria.pop('nick')
#             useras=g.db.getUserForNick(g.currentuser, nick)
#         else:
#             nick=None
#             useras=g.currentuser
#         throwawaycontext=criteria.pop('context')
#         throwawayfqin=criteria.pop('fqin')
#         context="app"
#         taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqqn, criteria, fvlist, orderer)
#         return jsonify(taggings)#should this be just tags and not tags indexed by items? 

# #TODOAPI: do easy way of getting tags in grp: use spec methods
# #this could be way on onfly getting things into app. on other hand the deep routing should be doing all of this so we shouldnt have to call it.
# #the pythonic api equivqlent could be used for adding things in bulk. evan thats not particularly useful. I think we should not try and saveItem and such
# #but just concentrate on the posting. in this sense this is different from groups: the item must be saved, etc. BUG: Ok do it. Currently not touching
# @adsgut.route('/app/<appowner>/app:<appname>/itemsandtags', methods=['POST'])#user/name/itemtype/uri/tags=[[name, tagtype, description]...]
# def useritemtagapppost(appowner, appname):
#     #user=g.currentuser#The current user is doing the posting
#     #print "hello", user.nick
#     fqan=appowner+"/app:"+appname
#     app=g.db.getApp(g.currentuser, fqan)
#     if request.method == 'POST':
#         itspec={}
#         nick = request.form.get('userthere', None)
#         if nick:
#             useras=g.db.getUserForNick(g.currentuser, nick)
#         else:
#             useras=g.currentuser
#         itspec['creator']=useras
#         itspec['name'] = request.form.get('name', None)
#         if not itspec['name']:
#             doabort("BAD_REQ", "No name specified for item")
#         itspec['itemtype'] = request.form.get('itemtype', None)
#         if not itspec['itemtype']:
#             doabort("BAD_REQ", "No itemtype specified for item")
#         #print "world"
#         md5u=hashlib.md5()
#         itspec['uri']=request.form.get('uri', md5u.update(user.nickas+"/"+itspec['name']))
#         #itspec['description']=request.form.get('description', '')
#         #itspec['uri']=request.form.get('uri', ''
#         #print "aaa", itspec
#         item=g.dbp.saveItem(g.currentuser, useras, itspec)
#         item=g.dbp.postItemIntoApp(g.currentuser, useras, app, item)
#         g.dbp.commit()
#         g.dbp.commit()
#         tags=request.form.get('tags', [])#Empty array if no tags
#         tagobjects=[]
#         for tagname, tagtype, description in tags:
#             tagspec={}
#             tagspec['creator']=useras
#             tagspec['name'] = tagname
#             tagspec['tagtype'] = tagtype
#             tagspec['description']=description
#             tag, tagging=g.dbp.tagItem(g.currentuser, useras, item.fqin, tagspec)
#             it, ita=g.dbp.postTaggingIntoApp(g.currentuser, useras, app, item, tag)
#             g.dbp.commit()#move outside for speed when possible
#             tagobjects.append(ita.info())
#         return jsonify({'status':'OK', 'info':{'item':item.info(), 'apptaggings':tagobjects}})
#     else:
#         #doabort("BAD_REQ", "GET not supported")
#         criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
#         # if nick=='any':
#         #     useras=g.currentuser
#         # else:
#         #     useras=g.db.getUserForNick(g.currentuser, nick)
#         #     criteria['userthere']=True
#         if criteria.get(userthere)==True:
#             useras=criteria.pop('useras')
#         else:
#             useras=None
#         throwawaycontext=criteria.pop('context')
#         throwawayfqin=criteria.pop('fqin')
#         context="app"
#         fqin=fqan
#         taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
#         return jsonify(taggings)
#######################################################################################################################
#These can be used as "am i saved" web services. Also gives groups and apps per item
#a 404 not found would be an ideal error
#BUG: are we properly protected. NO...check this..also shouldnt they be internal?
@adsgut.route('/item/<nick>/<ns>/<itemname>')
def usersitemget(nick, ns, itemname):
    user=g.db.getUserForNick(g.currentuser, nick)
    iteminfo=g.dbp.getItemByFqin(g.currentuser, ns+"/"+itemname)
    return jsonify({'item':iteminfo})

#should really be a query on user/nick/items but we do it separate as it gets one
@adsgut.route('/item/<nick>/byuri/<itemuri>')
def usersitembyuriget(nick, itemuri):
    user=g.db.getUserForNick(g.currentuser, nick)
    iteminfo=g.dbp.getItemByURI(g.currentuser, user, itemuri)
    return jsonify({'item':iteminfo})

#######################################################################################################################
# No aborts here for things not being there!
def _getQuery(querydict, fieldlist):
    criteria={}
    #only the stuff that comes in via fieldlist is allowed. This then acts as a sort of validation, or atleast, junk prevention.
    #this does not handle order_by, or such
    for ele, elev in fieldlist:
        qele=querydict.get(ele, elev)
        if ele in ['context', 'fqin']:
            criteria[ele]=qele
        elif ele=='userthere':
            if qele!=False:
                criteria['userthere']=True
                criteria['nick']=qele
            else:
                criteria['userthere']=False
        else:
            if qele:
                criteria[ele]=qele
    return criteria


#import classes
#from sqlalchemy import desc




def _getItemQuery(querydict):
    fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None), ('userthere', False)]
    fieldvallist=['uri', 'name', 'whencreated', 'itemtype']
    orderer=querydict.getlist('order_by')
    return _getQuery(querydict, fieldlist), fieldvallist, orderer


def _getTagQuery(querydict):
    #one can combine name and tagtype to get, for example, tag:lensing
    fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('userthere', False)]
    fieldvallist=['tagname', 'tagtype', 'whentagged']
    orderer=querydict.getlist('order_by')
    return _getQuery(querydict, fieldlist), fieldvallist, orderer


def _getTagsForItemQuery(querydict):
    #one can combine name and tagtype to get, for example, tag:lensing
    fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('uri', ''), ('name', ''), ('itemtype', ''), ('userthere', False)]
    fieldvallist=['tagname', 'tagtype', 'whentagged', 'uri', 'whencreated', 'name', 'itemtype']
    orderer=querydict.getlist('order_by')
    return _getQuery(querydict, fieldlist), fieldvallist, orderer



#######################################################################################################################

#users items/posts
#currently get the items. worry about tags later
#think we'll do tags as tags=tagtype | all

# #query itemtype, context, fqin
# @adsgut.route('/user/<nick>/items')#q=fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
# def usersitems(nick):
#     #criteria, fvlist, orderer=_getQuery(request.args, [('itemtype',''), ('context', None), ('fqin', None)])
#     criteria, fvlist, orderer=_getItemQuery(request.args)
#     context=criteria.pop('context')
#     fqin=criteria.pop('fqin')
#     useras=g.db.getUserForNick(g.currentuser, nick)
#     criteria['userthere']=True
#     items=g.dbp.getItems(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
#     return jsonify({'items':items})

#query itemtype, tagtype, tagname? This is just a specialization of the above
# @adsgut.route('/user/<nick>/tags')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
# def userstags(nick):
#     criteria, fvlist, orderer=_getTagQuery(request.args)
#     context=criteria.pop('context')
#     fqin=criteria.pop('fqin')
#     user=g.db.getUserForNick(g.currentuser, nick)
#     if user==g.currentuser:
#         criteria['userthere']=True
#     taggings=g.dbp.getTaggingForItemspec(g.currentuser, user, context, fqin, criteria)
#     return jsonify(taggings)

# @adsgut.route('/user/<nick>/items/html')
# def usersitemshtml(nick):
#     criteria={}
#     user=g.db.getUserForNick(g.currentuser, nick)
#     criteria['userthere']=True
#     userinfo=user.info()
#     items=g.dbp.getItems(g.currentuser, user, None, None, criteria)
#     return render_template('usersaved.html', theuser=userinfo, items=items)

# #POST item
# #masqueradable BUT WE DONT SUPPORT IT FOR NOW
# #wait for useras/currentuser division.
# @adsgut.route('/items/<nick>', methods=['POST', 'GET'])#name/itemtype/uri/ #q=fieldlist=[('itemtype',''), ('context', None), ('fqin', None)]
# def useritempost(nick):
#     user=g.db.getUserForNick(g.currentuser, nick)
#     #print "hello", user.nick
#     if request.method == 'POST':
#         #print request.form
#         itspec={}
#         #nick = request.form.get('user', None)
#         itspec['creator']=user
#         itspec['name'] = request.form.get('name', None)
#         if not itspec['name']:
#             doabort("BAD_REQ", "No name specified for item")
#         itspec['itemtype'] = request.form.get('itemtype', None)
#         if not itspec['itemtype']:
#             doabort("BAD_REQ", "No itemtype specified for item")
#         #print "world"
#         md5u=hashlib.md5()
#         itspec['uri']=request.form.get('uri', md5u.update(user.nick+"/"+itspec['name']))
#         #itspec['description']=request.form.get('description', '')
#         #itspec['uri']=request.form.get('uri', ''
#         #print "aaa", itspec
#         newitem=g.dbp.saveItem(g.currentuser, user, itspec)
#         print "kkk", newitem
#         g.dbp.commit()#needed to get isoformats? YES
#         return jsonify({'status':'OK', 'info':newitem.info()})
#     else:
#         return usersitems(nick)

#query uri/name/itemtype
#BUG: this returns all items including tags and is thus farely useless. We dont want any inherited tables
#Can do this with a boolean or figure the sqlalchemyway
#But can be worked around currently using itemtype and such
@adsgut.route('/items', methods=['POST', 'GET'])##name/itemtype/uri/ #q=fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
def itemsbyany():
    #permit(g.currentuser!=None and g.currentuser.nick=='rahuldave', "wrong user")
    #useras=g.currentuser#???always support this? This one has complex permitting!!!
    if request.method=='POST':
        nick = request.form.get('userthere', None)
        if nick:
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            useras=g.currentuser
        itspec={}
        #nick = request.form.get('user', None)
        itspec['creator']=useras
        itspec['name'] = request.form.get('name', None)
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for item")
        itspec['itemtype'] = request.form.get('itemtype', None)
        if not itspec['itemtype']:
            doabort("BAD_REQ", "No itemtype specified for item")
        #print "world"
        md5u=hashlib.md5()
        itspec['uri']=request.form.get('uri', md5u.update(useras.nick+"/"+itspec['name']))
        #itspec['description']=request.form.get('description', '')
        #itspec['uri']=request.form.get('uri', ''
        #print "aaa", itspec
        newitem=g.dbp.saveItem(g.currentuser, useras, itspec)
        #it will do the autoposts with the correct tagmode
        g.dbp.commit()#needed to get isoformats? YES
        return jsonify({'status':'OK', 'info':newitem.info()})
    else:
        criteria, fvlist, orderer=_getItemQuery(request.args)
        if criteria.get('userthere')==True:
            nick=criteria.pop('nick')
            useras=g.db.getUserForNick(g.currentuser, nick)
        else:
            nick=None
            useras=g.currentuser
        #criteria['userthere']=True
        context=criteria.pop('context')
        fqin=criteria.pop('fqin')
        items=g.dbp.getItems(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
        return jsonify({'items':items})

# #add tagtype/tagname to query. Must this also be querying item attributes?
# @adsgut.route('/tags')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
# def tagsbyany():
#     useras=g.currentuser#BUG: always support this?
#     criteria, fvlist, orderer=_getTagQuery(request.args)
#     #criteria['userthere']=True
#     context=criteria.pop('context')
#     fqin=criteria.pop('fqin')
#     #This should be cleaned for values. BUG nor done yet. What i mean is wherever we get this we must make sure we get
#     #sensible values, consistent values
#     print 'CRITTER', criteria  
#     taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria)
#     return jsonify(taggings)
#######################################################################################################################

# @adsgut.route('/tags/<ns>/<itemname>')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
# def tagsforitem(ns, itemname):
#     criteria=_getTagQuery(request.args)
#     if criteria.get('userthere')==True:
#         nick=criteria.pop('nick')
#         useras=g.db.getUserForNick(g.currentuser, nick)
#     else:
#         nick=None
#         useras=g.currentuser
#     context=criteria.pop('context')
#     fqin=criteria.pop('fqin')
#     taggings=g.dbp.getTagsForItem(g.currentuser, user, ns+"/"+itemname, context, fqin, criteria)
#     return jsonify(taggings)

@adsgut.route('/items/<ns>/<tagspace>/<tagtypename>:<tagname>')#q=fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
def itemsfortag(ns, tagspace, tagtypename, tagname):
    criteria, fvlist, orderer=_getItemQuery(request.args)
    if criteria.get('userthere')==True:
        nick=criteria.pop('nick')
        useras=g.db.getUserForNick(g.currentuser, nick)
    else:
        nick=None
        useras=g.currentuser
    tagtype=tagspace+"/"+tagtypename
    tag=ns+'/'+tagtype+":"+tagname
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    items=g.dbp.getItemsForTag(g.currentuser, useras, tag, context, fqin, criteria)
    return jsonify({'items':items})


#for groups/apps, as long as users are in them, one user can get the otherusers items and tags. Cool!
@adsgut.route('/tags')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('itemuri', ''), ('itemname', ''), ('itemtype', '')]
def tagsforitemspec():
    criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
    if criteria.get('userthere')==True:
        nick=criteria.pop('nick')
        useras=g.db.getUserForNick(g.currentuser, nick)
    else:
        nick=None
        useras=g.currentuser
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
    return jsonify(taggings)

@adsgut.route('/items/byspec')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('itemuri', ''), ('itemname', ''), ('itemtype', '')]
def itemsfortagspec():
    criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
    if criteria.get('userthere')==True:
        nick=criteria.pop('nick')
        useras=g.db.getUserForNick(g.currentuser, nick)
    else:
        nick=None
        useras=g.currentuser
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    print "userAS", useras.nick, g.currentuser.nick 
    items=g.dbp.getItemsForTagspec(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
    return jsonify(items)

#######################################################################################################################
#These too are redundant but we might want to support them as a different uri scheme
#######################################################################################################################
#redundant, i think
# @adsgut.route('/tags/<username>/<tagtype>:<tagname>')
# def dogroup(username, tagtype, tagname):
#     fqgn = username+'/group:'+groupname
#     groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
#     return jsonify(**groupinfo)


# @adsgut.route('/tags/<tagtype>:<tagname>/')
# def group_users(tagtype, tagname):
#     fqgn = username+'/group:'+groupname
#     users=g.db.usersInGroup(g.currentuser,fqgn)
#     return jsonify({'users':users})

#######################################################################################################################
#######################################################################################################################

if __name__=="__main__":
    adsgut.run(debug=True)
#######################################################################################################################

