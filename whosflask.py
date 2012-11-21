from dbase import setup_db
import whos, posts
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, escape, make_response, jsonify, Blueprint
import sys, os
import hashlib
from permissions import permit
from errors import abort
engine, db_session=setup_db("/tmp/adsgut.db")



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
#BUG: redo this with new user system

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

#use this for op based POSTS?
#currentuser=g.db.getCurrentuser(session.username)
#GET for info
@adsgut.route('/user/<nick>')
def douser(nick):
    userinfo=g.db.getUserInfo(g.currentuser, nick)
    return jsonify(**userinfo)

@adsgut.route('/user/<nick>/profile/html')
def profile(nick):
    userinfo=g.db.getUserInfo(g.currentuser, nick)
    return render_template('userprofile.html', theuser=userinfo)

@adsgut.route('/user/<nick>/groupsin')
def groupsin(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.groupsForUser(g.currentuser, user)
    return jsonify({'groups':groups})

@adsgut.route('/user/<nick>/groupsowned')
def groupsowned(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.ownerOfGroups(g.currentuser, user)
    return jsonify({'groups':groups})

#BUG: these returns group info for each group. permits must make sure there is no leakage
# in classes, we may need to have different functions for info that needs to be embargoed.
#but thats the right level at which to do it. also means that permit may need to not just
#raise exceptions, but respond on an if-then basis. (permitwitherror?)

@adsgut.route('/user/<nick>/groupsinvited')
def groupsinvited(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.groupInvitationsForUser(g.currentuser, user)
    return jsonify({'groups':groups})

@adsgut.route('/user/<nick>/appsin')
def appsin(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.appsForUser(g.currentuser, user)
    return jsonify({'apps':apps})

@adsgut.route('/user/<nick>/appsowned')
def appsowned(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.ownerOfApps(g.currentuser, user)
    return jsonify({'apps':apps})

#use this for the email invitation?
@adsgut.route('/user/<nick>/appsinvited')
def appsinvited(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.appInvitationsForUser(g.currentuser, user)
    return jsonify({'apps':apps})

#######################################################################################################################
#creating groups and apps
#accepting invites.
#DELETION methods not there BUG

@adsgut.route('/group', methods=['POST'])#groupname/description
def creategroup():
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
@adsgut.route('/group/<groupowner>/group:<groupname>/invitation', methods=['POST'])#user
def makeinvitetogroup(groupowner, groupname):
    #add permit to match user with groupowner
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        nick=request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "No User Specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        g.db.inviteUserToGroup(g.currentuser, fqgn, user, None)
        g.db.commit()
        return jsonify({'status':'OK', 'info': {'invited':nick, 'to':fqgn}})
    else:
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/group/<groupowner>/group:<groupname>/acceptinvitation', methods=['POST'])#accepr
def acceptinvitetogroup(nick, groupowner, groupname):  
    user=g.currentuser
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        accept=request.form.get('accept', 'NA')
        if accept==True:
            g.db.acceptInviteToGroup(g.currentuser, fqgn, user, None)
            g.db.commit()
            return jsonify({'status':'OK', 'info': {'invited':nick, 'to': fqgn, 'accepted':True}})
        elif accept==False:
            return jsonify({'status': 'OK', 'info': {'invited':nick, 'to': fqgn, 'accepted':False}})
        else:
            doabort("BAD_REQ", "accept not provided")
    else:
        doabort("BAD_REQ", "GET not supported")

#This is used for bulk addition of a user. Whats the usecase? current perms protect this
#BUG: maybe add a bulk version?
@adsgut.route('/group/<groupowner>/group:<groupname>/users', methods=['GET', 'POST'])#user
def addusertogrouporgroupusers(groupowner, groupname):
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
        return jsonify({'users':users})

# @adsgut.route('/group/<username>/group:<groupname>/users')
# def group_users(username, groupname):
#     fqgn = username+'/group:'+groupname
#     users=g.db.usersInGroup(g.currentuser,fqgn)
#     return jsonify({'users':users})

@adsgut.route('/app', methods=['POST'])#name/description
def createapp():
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
        newapp=g.db.addApplication(g.currentuser, user, appspec)
        g.db.commit()
        return jsonify({'status':'OK', 'info':newapp.info()})
    else:
        doabort("BAD_REQ", "GET not supported")

#Currently wont allow you to create app, or accept invites to apps
@adsgut.route('/app/<appowner>/app:<appname>/invitation', methods=['POST'])#user
def makeinvitetoapp(appowner, appname):
    #add permit to match user with groupowner
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        nick=request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "No User Specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        g.db.inviteUserToApp(g.currentuser, fqan, user, None)
        g.db.commit()
        return jsonify({'status':'OK',  'info': {'invited':nick, 'to': fqan}})
    else:
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/app/<appowner>/app:<appname>/acceptinvitation', methods=['POST'])#accept
def acceptinvitetoapp(nick, appowner, appname):  
    user=g.currentuser
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        accept=request.form.get('accept', 'NA')
        if accept==True:
            g.db.acceptInviteToApp(g.currentuser, fqan, user, None)
            g.db.commit()
            return jsonify({'status':'OK','info': {'invited':nick, 'to': fqan, 'accepted':True}})
        elif accept==False:
            return jsonify({'status': 'OK', 'info': {'invited':nick, 'to': fqan, 'accepted':False}})
        else:
            doabort("BAD_REQ", "accept not provided")
    else:
        doabort("BAD_REQ", "GET not supported")

#Whats the use case for this? bulk app adds which dont go through invites.
@adsgut.route('/app/<appowner>/app:<appname>/users', methods=['GET', 'POST'])#user
def addusertoapporappusers(appowner, appname):
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
        return jsonify({'users':users}) 


@adsgut.route('/app/<appowner>/app:<appname>/groups', methods=['GET', 'POST'])#group
def addgrouptoapporappgroups(appowner, appname):
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
        return jsonify({'groups':groups})  
#######################################################################################################################

#POST/GET
@adsgut.route('/group/html')
def creategrouphtml():
    pass

#get group info
@adsgut.route('/group/<username>/group:<groupname>')
def dogroup(username, groupname):
    fqgn = username+'/group:'+groupname
    groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
    return jsonify(**groupinfo)

@adsgut.route('/group/<username>/group:<groupname>/profile/html')
def group_profile(username, groupname):
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
def doapp(username, appname):
    fqan = username+'/app:'+appname
    appinfo=g.db.getAppInfo(g.currentuser, fqan)
    return jsonify(**appinfo)

@adsgut.route('/app/<username>/app:<appname>/profile/html')
def app_profile(username, appname):
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

#POST item
#masqueradable BUT WE DONT SUPPORT IT FOR NOW
@adsgut.route('/items/<nick>', methods=['POST'])#name/itemtype/uri/
def useritempost(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    #print "hello", user.nick
    if request.method == 'POST':
        #print request.form
        itspec={}
        #nick = request.form.get('user', None)
        itspec['creator']=user
        itspec['name'] = request.form.get('name', None)
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for item")
        itspec['itemtype'] = request.form.get('itemtype', None)
        if not itspec['itemtype']:
            doabort("BAD_REQ", "No itemtype specified for item")
        #print "world"
        md5u=hashlib.md5()
        itspec['uri']=request.form.get('uri', md5u.update(user.nick+"/"+itspec['name']))
        #itspec['description']=request.form.get('description', '')
        #itspec['uri']=request.form.get('uri', ''
        #print "aaa", itspec
        newitem=g.dbp.saveItem(g.currentuser, user, itspec)
        print "kkk", newitem
        g.dbp.commit()#needed to get isoformats? YES
        return jsonify({'status':'OK', 'info':newitem.info()})
    else:
        doabort("BAD_REQ", "GET not supported")

#POST tag
#masqueradable BUT WE DONT SUPPORT IT FOR NOW
@adsgut.route('/tags/<nick>/<ns>/<itemname>', methods=['GET', 'POST'])#tagname/tagtype/description #q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
def usertagpost(nick, itemname):
    user=g.db.getUserForNick(g.currentuser, nick)
    nsuser=g.db.getUserForNick(g.currentuser, ns)# can be any user..but will it fail if currentuser is not nsuser? NO, good
    #print "hello", user.nick
    if request.method == 'POST':
        #print request.form
        tagspec={}
        tagspec['creator']=user
        tagspec['name'] = request.form.get('tagname', None)
        if not tagspec['name']:
            doabort('BAD_REQ', "No name specified for tag")
        tagspec['tagtype'] = request.form.get('tagtype', None)
        if not tagspec['tagtype']:
            doabort('BAD_REQ', "No tagtype specified for tag")
        #print "world"
        #md5u=hashlib.md5()
        #itspec['uri']=request.form.get('uri', md5u.update(creator+"/"+name))
        if request.form.has_key('description'):
            tagspec['description']=request.form['description']
        #print "aaa", itspec
        iteminfo=g.dbp.getItemByFqin(g.currentuser, nsuser.nick+"/"+itemname)
        newtag, newtagging=g.dbp.tagItem(g.currentuser, user, iteminfo['fqin'], tagspec)
        #print "kkk"
        g.dbp.commit()
        #returning the taggings requires a commit at this point
        return jsonify({'status':'OK', 'info':{'item': iteminfo['fqin'], 'tagging':newtagging.info()}})
    else:
        criteria, fvlist, orderer=_getTagQuery(request.args)
        context=criteria.pop('context')
        fqin=criteria.pop('fqin')
        user=g.db.getUserForNick(g.currentuser, nick)
        taggings=g.dbp.getTagsForItem(g.currentuser, user, ns+"/"+itemname, context, fqin, criteria)
        return jsonify(taggings)


@adsgut.route('/tags/<nick>/<ns>/<itemname>/multi', methods=['GET', 'POST'])#taginfos=[{tagname/tagtype/description}] #q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
def usermultitagpost(nick, itemname):
    user=g.db.getUserForNick(g.currentuser, nick)
    nsuser=g.db.getUserForNick(g.currentuser, ns)
    #print "hello", user.nick
    if request.method == 'POST':
        #print request.form
        
        #print "aaa", itspec#
        iteminfo=g.dbp.getItemByFqin(g.currentuser, nsuser.nick+"/"+itemname)
        taginfos=request.form.get('taginfos', [])
        newtaggings=[]
        for ti in taginfos:
            if not ti['tagname']:
                doabort('BAD_REQ', "No names specified for tag")
            if not ti'tagtype']:
                doabort('BAD_REQ', "No tagtypes specified for tag")
            tagspec={}
            tagspec['creator']=user
            tagspec['name'] = ti['tagname']           
            tagspec['tagtype'] = ti['tagtype']       
            if ti.has_key('description'):
                tagspec['description']=ti['description']
            newtag, newtagging=g.dbp.tagItem(g.currentuser, user, iteminfo['fqin'], tagspec)
            newtaggings.append[newtagging]
        #print "kkk"
        g.dbp.commit()
        #returning the taggings requires a commit at this point
        return jsonify({'status':'OK', 'info':{'item': iteminfo['fqin'], 'tagging':[nt.info() for nt in newtaggings]}})
    else:
        criteria, fvlist, orderer=_getTagQuery(request.args)
        context=criteria.pop('context')
        fqin=criteria.pop('fqin')
        user=g.db.getUserForNick(g.currentuser, nick)
        taggings=g.dbp.getTagsForItem(g.currentuser, user, ns+"/"+itemname, context, fqin, criteria)
        return jsonify(taggings)
#######################################################################################################################
#Post to group and post to app. We are nor supporting any deletion web services as yet.
#Also post tag to group and post tag to app. tag too must be saved and lookupable
#BUG: we must solve the whose items u can post problem as posting currently (for saving, atleast seems to use
#the current user)

#Currently we only support currentuser=useras. Support for authtoken soon. BUG
#perhaps sstemuser should be tested first?

#@adsgut.route('/item/<ns>/<itemname>/grouppost', methods=['POST'])#user/fqin
@adsgut.route('/group/<groupowner>/group:<groupname>/items', methods=['POST'])#user/fqin
def useritemgrouppost(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqin = request.form.get('fqin', None)
        if not fqin:
            doabort("BAD_REQ", "Item to post to group not specified")
        nick = request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "User doing posting not specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        fqgn=groupowner+"/group:"+groupname
        item=g.dbp.postItemIntoGroup(g.currentuser, user, fqgn, fqin)
        g.dbp.commit()
        return jsonify({'status':'OK', 'info':{'item':item.info(), 'group':fqgn}})
    else:
        #later support via GET all items in group, perhaps based on spec
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/groups/<nick>/<ns>/<itemname>/multi', methods=['POST'])#fqins=[fqin]
def useritemmultigrouppost(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    user=g.db.getUserForNick(g.currentuser, nick)
    nsuser=g.db.getUserForNick(g.currentuser, ns)
    iteminfo=g.dbp.getItemByFqin(g.currentuser, nsuser.nick+"/"+itemname)
    fqin=iteminfo['fqin']
    if request.method == 'POST':
        fqins = request.form.get('fqins', None)
        if not fqins:
            doabort("BAD_REQ", "groups not specified")
        for fqgn in fqins:
            item=g.dbp.postItemIntoGroup(g.currentuser, user, fqgn, fqin)
        g.dbp.commit()
        return jsonify({'status':'OK', 'info':{'item':item.info(), 'groups':[fqgn for fqgn in fqins]}})
    else:
        #later support via GET all items in group, perhaps based on spec
        doabort("BAD_REQ", "GET not supported")

#@adsgut.route('/item/<ns>/<itemname>/apppost', methods=['POST'])#user/fqin
@adsgut.route('/app/<appowner>/app:<appname>/items', methods=['POST'])#user/fqin
def useritemapppost(ns, itemname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqin = request.form.get('fqin', None)
        if not fqin:
            doabort("BAD_REQ", "Item to post to app not specified")
        nick = request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "User doing posting not specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        fqan=appowner+"/app:"+appname
        item=g.dbp.postItemToGroup(g.currentuser, user, fqan, fqin)
        g.dbp.commit()
        return jsonify({'status':'OK', 'info':{'item':item.info(), 'app':fqan}})
    else:
        #later support via GET all items in app, perhaps based on spec
        doabort("BAD_REQ", "GET not supported")

#@adsgut.route('/tag/<ns>/<itemname>/grouppost', methods=['POST'])#user/fqin/fqtn
#How should this be presented in GET?
@adsgut.route('/group/<groupowner>/group:<groupname>/tags', methods=['POST'])#user/fqin/fqtn
def usertaggrouppost(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        fqin = request.form.get('fqin', None)
        if not fqin:
            doabort("BAD_REQ", "item whos tags are to posted to group not specified")
        fqtn = request.form.get('fqtn', None)
        if not fqtn:
            doabort("BAD_REQ", "Tag to post to group not specified")
        nick = request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "User doing posting not specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        it, itg=g.dbp.postTaggingIntoGroup(g.currentuser, user, fqgn, fqin, fqtn)
        g.dbp.commit()
        return jsonify({'status':'OK', 'info': itg.info()})
    else:
        doabort("BAD_REQ", "GET not supported")

#This posts an item, its tags, and all that to a single group

@adsgut.route('/group/<groupowner>/group:<groupname>/itemsandtags', methods=['POST'])#user/name/itemtype/uri/tags=[[name, tagtype, description]...]
def useritemtaggrouppost(groupowner, groupname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    fqgn=groupowner+"/group:"+groupname
    grp=g.db.getGroup(g.currentuser, fqgn)
    if request.method == 'POST':
        itspec={}
        nick = request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "User doing posting not specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        itspec['creator']=user
        itspec['name'] = request.form.get('name', None)
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for item")
        itspec['itemtype'] = request.form.get('itemtype', None)
        if not itspec['itemtype']:
            doabort("BAD_REQ", "No itemtype specified for item")
        #print "world"
        md5u=hashlib.md5()
        itspec['uri']=request.form.get('uri', md5u.update(user.nick+"/"+itspec['name']))
        #itspec['description']=request.form.get('description', '')
        #itspec['uri']=request.form.get('uri', ''
        #print "aaa", itspec
        item=g.dbp.saveItem(g.currentuser, user, itspec)
        item=g.dbp.postItemIntoGroup(g.currentuser, user, grp, item)
        g.dbp.commit()
        tags=request.form.get('tags', [])#Empty array if no tags
        tagobjects=[]
        for tagname, tagtype, description in tags:
            tagspec={}
            tagspec['creator']=user
            tagspec['name'] = tagname
            tagspec['tagtype'] = tagtype
            tagspec['description']=description
            tag, tagging=g.dbp.tagItem(g.currentuser, user, item.fqin, tagspec)
            it, itg=g.dbp.postTaggingIntoGroup(g.currentuser, user, grp, item, tag)
            g.dbp.commit() # move outside to make faster
            tagobjects.append(itg.info())
        return jsonify({'status':'OK', 'info':{'item':item.info(), 'grouptaggings':tagobjects}})
    else:
        doabort("BAD_REQ", "GET not supported")

#@adsgut.route('/tag/<ns>/<itemname>/apppost', methods=['POST'])#user/fqin/fqtn
@adsgut.route('/app/<appowner>/app:<appname>/tags', methods=['POST'])#user/fqin/fqtn
def usertagapppost(appowner, appname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        fqan = request.form.get('fqin', None)
        if not fqan:
            doabort("BAD_REQ", "item whos tags are to posted to app not specified")
        fqtn = request.form.get('fqtn', None)
        if not fqtn:
            doabort("BAD_REQ", "Tag to post to app not specified")
        nick = request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "User doing posting not specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        it, ita = g.dbp.postTaggingIntoApp(g.currentuser, user, fqan, fqin, fqtn)
        g.dbp.commit()
        return jsonify({'status':'OK', 'info': ita.info()})
    else:
        doabort("BAD_REQ", "GET not supported")  

@adsgut.route('/app/<appowner>/app:<appname>/itemsandtags', methods=['POST'])#user/name/itemtype/uri/tags=[[name, tagtype, description]...]
def useritemtagapppost(appowner, appname):
    #user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    fqan=appowner+"/app:"+appname
    app=g.db.getApp(g.currentuser, fqan)
    if request.method == 'POST':
        itspec={}
        nick = request.form.get('user', None)
        if not nick:
            doabort("BAD_REQ", "User doing posting not specified")
        user=g.db.getUserForNick(g.currentuser, nick)
        itspec['creator']=user
        itspec['name'] = request.form.get('name', None)
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for item")
        itspec['itemtype'] = request.form.get('itemtype', None)
        if not itspec['itemtype']:
            doabort("BAD_REQ", "No itemtype specified for item")
        #print "world"
        md5u=hashlib.md5()
        itspec['uri']=request.form.get('uri', md5u.update(user.nick+"/"+itspec['name']))
        #itspec['description']=request.form.get('description', '')
        #itspec['uri']=request.form.get('uri', ''
        #print "aaa", itspec
        item=g.dbp.saveItem(g.currentuser, user, itspec)
        item=g.dbp.postItemIntoApp(g.currentuser, user, app, item)
        g.dbp.commit()
        g.dbp.commit()
        tags=request.form.get('tags', [])#Empty array if no tags
        tagobjects=[]
        for tagname, tagtype, description in tags:
            tagspec={}
            tagspec['creator']=user
            tagspec['name'] = tagname
            tagspec['tagtype'] = tagtype
            tagspec['description']=description
            tag, tagging=g.dbp.tagItem(g.currentuser, user, item.fqin, tagspec)
            it, ita=g.dbp.postTaggingIntoApp(g.currentuser, user, app, item, tag)
            g.dbp.commit()#move outside for speed when possible
            tagobjects.append(ita.info())
        return jsonify({'status':'OK', 'info':{'item':item.info(), 'apptaggings':tagobjects}})
    else:
        doabort("BAD_REQ", "GET not supported")
#######################################################################################################################
#These can be used as "am i saved" web services. Also gives groups and apps per item
#a 404 not found would be an ideal error
#BUG: are we properly protected. NO
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
    for ele, elev in fieldlist:
        qele=querydict.get(ele, elev)
        if ele in ['context', 'fqin']:
            criteria[ele]=qele
        else:
            if qele:
                criteria[ele]=qele
    return criteria


#import classes
#from sqlalchemy import desc




def _getItemQuery(querydict):
    fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
    fieldvallist=['uri', 'name', 'whencreated', 'itemtype']
    orderer=querydict.getlist('order_by')
    return _getQuery(querydict, fieldlist), fieldvallist, orderer


def _getTagQuery(querydict):
    #one can combine name and tagtype to get, for example, tag:lensing
    fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
    fieldvallist=['tagname', 'tagtype', 'whentagged']
    orderer=querydict.getlist('order_by')
    return _getQuery(querydict, fieldlist), fieldvallist, orderer


def _getTagsForItemQuery(querydict):
    #one can combine name and tagtype to get, for example, tag:lensing
    fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('uri', ''), ('name', ''), ('itemtype', '')]
    fieldvallist=['tagname', 'tagtype', 'whentagged', 'uri', 'whencreated', 'name', 'itemtype']
    orderer=querydict.getlist('order_by')
    return _getQuery(querydict, fieldlist), fieldvallist, orderer



#query uri/name/itemtype
#BUG: this returns all items including tags and is thus farely useless. We dont want any inherited tables
#Can do this with a boolean or figure the sqlalchemyway
#But can be worked around currently using itemtype and such
@adsgut.route('/items')#q=fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
def itemsbyany():
    #permit(g.currentuser!=None and g.currentuser.nick=='rahuldave', "wrong user")
    useras=g.currentuser#BUG: always support this?
    criteria, fvlist, orderer=_getItemQuery(request.args)
    #criteria['userthere']=True
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.   
    items=g.dbp.getItems(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
    return jsonify({'items':items})

#add tagtype/tagname to query. Must this also be querying item attributes?
@adsgut.route('/tags')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
def tagsbyany():
    useras=g.currentuser#BUG: always support this?
    criteria, fvlist, orderer=_getTagQuery(request.args)
    #criteria['userthere']=True
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet. 
    print 'CRITTER', criteria  
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria)
    return jsonify(taggings)
#######################################################################################################################
#tagging based on item spec. BUG: how are we guaranteeing name unique amongst a user. Must specify joint unique for items

# @adsgut.route('/tags/<nick>/<ns>/<itemname>')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
# def tagsforitem(nick, ns, itemname):
#     criteria=_getTagQuery(request.args)
#     context=criteria.pop('context')
#     fqin=criteria.pop('fqin')
#     user=g.db.getUserForNick(g.currentuser, nick)
#     taggings=g.dbp.getTagsForItem(g.currentuser, user, ns+"/"+itemname, context, fqin, criteria)
#     return jsonify(taggings)

@adsgut.route('/items/<nick>/<tagspace>/<tagtypename>:<tagname>')#q=fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
def itemsfortag(nick, tagspace, tagtypename, tagname):
    tagtype=tagspace+"/"+tagtypename
    criteria, fvlist, orderer=_getItemQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    items=g.dbp.getItemsForTag(g.currentuser, user, nick+'/'+tagtype+":"+tagname, context, fqin, criteria)
    return jsonify({'items':items})


#for groups/apps, as long as users are in them, one user can get the otherusers items and tags. Cool!
@adsgut.route('/tags/<nick>/byspec')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('itemuri', ''), ('itemname', ''), ('itemtype', '')]
def tagsforitemspec(nick):
    criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
    if nick=='any':
        useras=g.currentuser
    else:
        useras=g.db.getUserForNick(g.currentuser, nick)
        criteria['userthere']=True
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.   
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
    return jsonify(taggings)

@adsgut.route('/items/<nick>/byspec')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('itemuri', ''), ('itemname', ''), ('itemtype', '')]
def itemsfortagspec(nick):
    criteria, fvlist, orderer=_getTagsForItemQuery(request.args)
    print "nick", nick, g, g.currentuser
    if nick=='any':
        useras=g.currentuser
    else:
        useras=g.db.getUserForNick(g.currentuser, nick)
        criteria['userthere']=True
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.  
    print "userAS", useras.nick, g.currentuser.nick 
    items=g.dbp.getItemsForTagspec(g.currentuser, useras, context, fqin, criteria, fvlist, orderer)
    return jsonify(items)
#######################################################################################################################

#users items/posts
#currently get the items. worry about tags later
#think we'll do tags as tags=tagtype | all

#query itemtype, context, fqin
@adsgut.route('/user/<nick>/items')#q=fieldlist=[('itemtype',''), ('context', None), ('fqin', None)]
def usersitems(nick):
    #criteria, fvlist, orderer=_getQuery(request.args, [('itemtype',''), ('context', None), ('fqin', None)])
    criteria, fvlist, orderer=_getItemQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    # if user==g.currentuser: This throws a bug. remove BUG
    #     criteria['userthere']=True
    criteria['userthere']=True
    items=g.dbp.getItems(g.currentuser, user, context, fqin, criteria, fvlist, orderer)
    return jsonify({'items':items})

#query itemtype, tagtype, tagname? This is just a specialization of the above
@adsgut.route('/user/<nick>/tags')#q=fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
def userstags(nick):
    criteria, fvlist, orderer=_getTagQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    if user==g.currentuser:
        criteria['userthere']=True
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, user, context, fqin, criteria)
    return jsonify(taggings)

@adsgut.route('/user/<nick>/items/html')
def usersitemshtml(nick):
    criteria={}
    user=g.db.getUserForNick(g.currentuser, nick)
    criteria['userthere']=True
    userinfo=user.info()
    items=g.dbp.getItems(g.currentuser, user, None, None, criteria)
    return render_template('usersaved.html', theuser=userinfo, items=items)

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

