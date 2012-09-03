from dbase import setup_db
import whos, posts
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, escape, make_response, jsonify

import hashlib
from permissions import permit
from errors import abort
engine, db_session=setup_db("/tmp/adsgut.db")
app = Flask(__name__)

#######################################################################################################################

@app.before_request
def before_request():
        #g.db=whos.Whosdb(db_session)
        g.dbp=posts.Postdb(db_session)
        g.db=g.dbp.whosdb
        if session.has_key('username'):
            g.currentuser=g.db.getUserForNick(None, session['username'])
        else:
            g.currentuser=None

@app.teardown_request
def shutdown_session(exception=None):
    g.db.commit()
    g.db.remove()

#EXPLICITLY COMMIT ON POSTS. THOUGH TO DO MULTIPLE THINGS, WE MAY WANT TO 
#SCHEDULE COMMITS SEPARATELY..really commits not a property of whosdb
#currently explicit for simplicity

#######################################################################################################################

@app.route('/all')
def indexall():
    return render_template('allindex.html', users=g.db.allUsers(g.currentuser), 
        groups=g.db.allGroups(g.currentuser), apps=g.db.allApps(g.currentuser))

@app.route('/')
def index():
    return render_template('index.html', suppressed=True, poal=True)

#######################################################################################################################
@app.route('/poal')
def poal():
    return render_template('poal.html', users=g.db.allUsers(g.currentuser), 
        groups=g.db.allGroups(g.currentuser), apps=g.db.allApps(g.currentuser), poal=True)

#######################################################################################################################
#BUG: redo this with new user system

@app.route('/login', methods=['GET', 'POST'])
def login():
    error=None
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['logged_in'] = True
        flash('You were logged in')
        return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout')
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
@app.route('/user/<nick>')
def douser(nick):
    userinfo=g.db.getUserInfo(g.currentuser, nick)
    return jsonify(**userinfo)

@app.route('/user/<nick>/profile/html')
def profile(nick):
    userinfo=g.db.getUserInfo(g.currentuser, nick)
    return render_template('userprofile.html', theuser=userinfo)

@app.route('/user/<nick>/groupsin')
def groupsin(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.groupsForUser(g.currentuser, user)
    return jsonify({'groups':groups})

@app.route('/user/<nick>/groupsowned')
def groupsowned(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.ownerOfGroups(g.currentuser, user)
    return jsonify({'groups':groups})

#BUG: these returns group info for each group. permits must make sure there is no leakage
# in classes, we may need to have different functions for info that needs to be embargoed.
#but thats the right level at which to do it. also means that permit may need to not just
#raise exceptions, but respond on an if-then basis. (permitwitherror?)

@app.route('/user/<nick>/groupsinvited')
def groupsinvited(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    groups=g.db.groupInvitationsForUser(g.currentuser, user)
    return jsonify({'groups':groups})

@app.route('/user/<nick>/appsin')
def appsin(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.appsForUser(g.currentuser, user)
    return jsonify({'apps':apps})

@app.route('/user/<nick>/appsowned')
def appsowned(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.ownerOfApps(g.currentuser, user)
    return jsonify({'apps':apps})

#use this for the email invitation?
@app.route('/user/<nick>/appsinvited')
def appsinvited(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    apps=g.db.appInvitationsForUser(g.currentuser, user)
    return jsonify({'apps':apps})

#######################################################################################################################
#creating groups and apps
#accepting invites.
#DELETION methods not there BUG

@app.route('/group', methods=['post'])
def creategroup():
    user=g.currentuser
    groupspec={}
    if request.method == 'POST':
        groupname=request.form['name']
        description=request.form.get('description', '')
        groupspec['creator']=user
        groupspec['name']=groupname
        groupspec['description']=description
        g.db.addGroup(g.currentuser, user, groupspec)
        return jsonify({'status':'OK'})
    else:
        return None

#Currently wont allow you to create app, or accept invites to apps
@app.route('/group/<groupowner>/group:<groupname>/invitation', methods=['post'])
def makeinvitetogroup(groupowner, groupname):
    #add permit to match user with groupowner
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        nick=request.POST['user']
        user=g.db.getUserForNick(g.currentuser, nick)
        g.db.inviteUserToGroup(g.currentuser, fqgn, user, None)
        return jsonify({'status':'OK'})
    else:
        return None

@app.route('/groupinvite/<groupowner>/group:<groupname>', methods=['post'])
def acceptinvitetogroup(nick, groupowner, groupname):  
    user=g.currentuser
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        accept=request.form.get('accept', None)
        if accept:
            g.db.acceptInviteToGroup(g.currentuser, fqgn, None)
            return jsonify({'status':'OK'})
        else:
            return None
    else:
        return None


@app.route('/app', methods=['post'])
def createapp():
    user=g.currentuser
    appspec={}
    if request.method == 'POST':
        appname=request.form['name']
        description=request.form.get('description', '')
        appspec['creator']=user
        appspec['name']=groupname
        appspec['description']=description
        g.db.addApplication(g.currentuser, user, appspec)
        return jsonify({'status':'OK'})
    else:
        return None

#Currently wont allow you to create app, or accept invites to apps
@app.route('/app/<appowner>/app:<appname>/invitation', methods=['post'])
def makeinvitetoapp(appowner, appname):
    #add permit to match user with groupowner
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        nick=request.POST['user']
        user=g.db.getUserForNick(g.currentuser, nick)
        g.db.inviteUserToApp(g.currentuser, fqan, user, None)
        return jsonify({'status':'OK'})
    else:
        return None

@app.route('/appinvite/<appowner>/app:<appname>', methods=['post'])
def acceptinvitetoapp(nick, appowner, appname):  
    user=g.currentuser
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        accept=request.form.get('accept', None)
        if accept:
            g.db.acceptInviteToApp(g.currentuser, fqan, None)
            return jsonify({'status':'OK'})
        else:
            return None
    else:
        return None

    
#######################################################################################################################

#POST item
@app.route('/item/<nick>', methods=['POST'])
def useritempost(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    #print "hello", user.nick
    if request.method == 'POST':
        #print request.form
        itspec={}
        itspec['creator']=user
        itspec['name'] = request.form['name']
        itspec['itemtype'] = request.form['itemtype']
        #print "world"
        #md5u=hashlib.md5()
        #itspec['uri']=request.form.get('uri', md5u.update(creator+"/"+name))
        itspec['uri']=request.form['uri']
        #print "aaa", itspec
        g.dbp.saveItem(g.currentuser, user, itspec)
        #print "kkk"
        return jsonify({'status':'OK'})
    else:
        return None

#POST tag
@app.route('/tag/<nick>/<itemname>', methods=['POST'])
def usertagpost(nick, itemname):
    user=g.db.getUserForNick(g.currentuser, nick)
    #print "hello", user.nick
    if request.method == 'POST' and itemname==None:
        #print request.form
        tagspec={}
        tagspec['creator']=user
        tagspec['name'] = request.form['name']
        tagspec['tagtype'] = request.form['tagtype']
        #print "world"
        #md5u=hashlib.md5()
        #itspec['uri']=request.form.get('uri', md5u.update(creator+"/"+name))
        if request.form.has_key('description'):
            tagspec['description']=request.form['description']
        #print "aaa", itspec
        iteminfo=g.dbp.getItemByName(g.currentuser, user, itemname)
        g.dbp.tagItem(g.currentuser, user, iteminfo['fqin'], tagspec)
        #print "kkk"
        return jsonify({'status':'OK'})
    else:
        return None

#######################################################################################################################
#Post to group and post to app. We are nor supporting any deletion web services as yet.
#Also post tag to group and post tag to app. tag too must be saved and lookupable
#BUG: we must solve the whose items u can post problem as posting currently (for saving, atleast seems to use
#the current user)
@app.route('/item/<nick>/<itemname>/grouppost', methods=['POST'])
def useritemgrouppost(nick, itemname):
    user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqgn = request.form['fqin']
        g.dbp.postItemToGroup(g.currentuser, user, fqgn, nick+"/"+itemname)
        return jsonify({'status':'OK'})
    else:
        return None

@app.route('/item/<nick>/apppost', methods=['POST'])
def useritemapppost(nick):
    user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqan = request.form['fqin']
        g.dbp.postItemToGroup(g.currentuser, user, fqan, nick+"/"+itemname)
        return jsonify({'status':'OK'})
    else:
        return None

@app.route('/tag/<nick>/<itemname>/grouppost', methods=['POST'])
def usertaggrouppost(nick, itemname):
    user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqgn = request.form['fqin']
        fqtn = request.form['fqtn']
        g.dbp.postTaggingIntoGroup(g.currentuser, user, fqgn, nick+"/"+itemname, fqtn)
        return jsonify({'status':'OK'})
    else:
        return None

@app.route('/tag/<nick>/<itemname>/apppost', methods=['POST'])
def usertagapppost(nick, itemname):
    user=g.currentuser#The current user is doing the posting
    #print "hello", user.nick
    if request.method == 'POST':
        fqan = request.form['fqin']
        fqtn = request.form['fqtn']
        g.dbp.postTaggingIntoApp(g.currentuser, user, fqan, nick+"/"+itemname, fqtn)
        return jsonify({'status':'OK'})
    else:
        return None  

#######################################################################################################################
#These can be used as "am i saved" web services. Also gives groups and apps per item
#a 404 not found would be an ideal error
@app.route('/item/<nick>/<itemname>')
def usersitemget(nick, itemname):
    user=g.db.getUserForNick(g.currentuser, nick)
    iteminfo=g.dbp.getItemByName(g.currentuser, user, itemname)
    return jsonify({'item':iteminfo})

#should really be a query on user/nick/items but we do it separate as it gets one
@app.route('/itembyuri/<nick>/<itemuri>')
def usersitembyuriget(nick, itemuri):
    user=g.db.getUserForNick(g.currentuser, nick)
    iteminfo=g.dbp.getItemByURI(g.currentuser, user, itemuri)
    return jsonify({'item':iteminfo})

#######################################################################################################################

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

def _getItemQuery(querydict):
    fieldlist=[('uri',''), ('name',''), ('itemtype',''), ('context', None), ('fqin', None)]
    return _getQuery(querydict, fieldlist)

def _getTagQuery(querydict):
    #one can combine name and tagtype to get, for example, tag:lensing
    fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None)]
    return _getQuery(querydict, fieldlist)

#query uri/name/itemtype
#BUG: this returns all items including tags and is thus farely useless. We dont want any inherited tables
#Can do this with a boolean or figure the sqlalchemyway
#But can be worked around currently using itemtype and such
@app.route('/items')
def itemsbyany():
    #permit(g.currentuser!=None and g.currentuser.nick=='rahuldave', "wrong user")
    useras=g.currentuser
    criteria=_getItemQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.   
    items=g.dbp.getItems(g.currentuser, useras, context, fqin, criteria)
    return jsonify({'items':items})

#add tagtype/tagname to query. Must this also be querying item attributes?
@app.route('/tags')
def tagsbyany():
    useras=g.currentuser
    criteria=_getTagQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.   
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria)
    return jsonify(taggings)
#######################################################################################################################
#tagging based on item spec. BUG: how are we guaranteeing name unique amongst a user. Must specify joint unique for items

@app.route('/item/<nick>/<itemname>/tags')
def tagsforitem(nick, itemname):
    criteria=_getTagQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    taggings=g.dbp.getTagsForItem(g.currentuser, user, user.nick+'/'+itemname, context, fqin, criteria)
    return jsonify(taggings)

@app.route('/tag/<nick>/<tagspace>/<tagtypename>:<tagname>/items')
def itemsfortag(nick, tagspace, tagtypename, tagname):
    tagtype=tagspace+"/"+tagtypename
    criteria=_getItemQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    items=g.dbp.getItemsForTag(g.currentuser, user, nick+'/'+tagtype+":"+tagname, context, fqin, criteria)
    return jsonify({'items':items})

def _getTagsForItemQuery(querydict):
    #one can combine name and tagtype to get, for example, tag:lensing
    fieldlist=[('tagname',''), ('tagtype',''), ('context', None), ('fqin', None), ('itemuri', ''), ('itemname', ''), ('itemtype', '')]
    return _getQuery(querydict, fieldlist)

@app.route('/itemspec/<nick>/tags')
def tagsforitemspec(nick):
    criteria=_getTagsForItemQuery(request.args)
    if nick=='any':
        useras=g.currentuser
    else:
        useras=g.db.getUserForNick(g.currentuser, nick)
        criteria['userthere']=True
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.   
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, useras, context, fqin, criteria)
    return jsonify(taggings)

@app.route('/tagspec/<nick>/items')
def itemsfortagspec(nick):
    criteria=_getTagsForItemQuery(request.args)
    if nick=='any':
        useras=g.currentuser
    else:
        useras=g.db.getUserForNick(g.currentuser, nick)
        criteria['userthere']=True
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    #This should be cleaned for values. BUG nor done yet.   
    items=g.dbp.getItemsForTagspec(g.currentuser, useras, context, fqin, criteria)
    return jsonify(items)
#######################################################################################################################

#users items/posts
#currently get the items. worry about tags later
#think we'll do tags as tags=tagtype | all

#query itemtype, context, fqin
@app.route('/user/<nick>/items')
def usersitems(nick):
    criteria=_getQuery(request.args, [('itemtype',''), ('context', None), ('fqin', None)])
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    items=g.dbp.getItemsForUser(g.currentuser, user, context, fqin, criteria)
    return jsonify({'items':items})

#query itemtype, tagtype, tagname?
@app.route('/user/<nick>/tags')
def userstags(nick):
    criteria=_getTagQuery(request.args)
    context=criteria.pop('context')
    fqin=criteria.pop('fqin')
    user=g.db.getUserForNick(g.currentuser, nick)
    taggings=g.dbp.getTaggingForItemspec(g.currentuser, user, context, fqin, criteria)
    return jsonify(taggings)

@app.route('/user/<nick>/items/html')
def usersitemshtml(nick):
    user=g.db.getUserForNick(g.currentuser, nick)
    userinfo=user.info()
    items=g.dbp.getItemsForUser(g.currentuser, user)
    return render_template('usersaved.html', theuser=userinfo, items=items)

#######################################################################################################################
#These too are redundant but we might want to support them as a different uri scheme
#######################################################################################################################
#redundant, i think
# @app.route('/tags/<username>/<tagtype>:<tagname>')
# def dogroup(username, tagtype, tagname):
#     fqgn = username+'/group:'+groupname
#     groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
#     return jsonify(**groupinfo)


# @app.route('/tags/<tagtype>:<tagname>/')
# def group_users(tagtype, tagname):
#     fqgn = username+'/group:'+groupname
#     users=g.db.usersInGroup(g.currentuser,fqgn)
#     return jsonify({'users':users})

#######################################################################################################################
#######################################################################################################################

#POST/GET
@app.route('/group/html')
def creategrouphtml():
    pass

#get group info
@app.route('/group/<username>/group:<groupname>')
def dogroup(username, groupname):
    fqgn = username+'/group:'+groupname
    groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
    return jsonify(**groupinfo)

@app.route('/group/<username>/group:<groupname>/profile/html')
def group_profile(username, groupname):
    fqgn = username+'/group:'+groupname
    groupinfo=g.db.getGroupInfo(g.currentuser, fqgn)
    return render_template('groupprofile.html', thegroup=groupinfo)

@app.route('/group/<username>/group:<groupname>/users')
def group_users(username, groupname):
    fqgn = username+'/group:'+groupname
    users=g.db.usersInGroup(g.currentuser,fqgn)
    return jsonify({'users':users})


#TODO: do one for a groups apps

#######################################################################################################################
#######################################################################################################################

#POST/GET
@app.route('/app/html')
def createapphtml():
    pass

@app.route('/app/<username>/app:<appname>')
def doapp(username, appname):
    fqan = username+'/app:'+appname
    appinfo=g.db.getAppInfo(g.currentuser, fqan)
    return jsonify(**appinfo)

@app.route('/app/<username>/app:<appname>/profile/html')
def app_profile(username, appname):
    fqan = username+'/app:'+appname
    appinfo=g.db.getAppInfo(g.currentuser, fqan)
    return render_template('appprofile.html', theapp=appinfo)

@app.route('/app/<username>/app:<appname>/users')
def application_users(username, appname):
    fqan = username+'/app:'+appname
    users=g.db.usersInApp(g.currentuser,fqan)
    return jsonify({'users':users})


@app.route('/app/<username>/app:<appname>/groups')
def application_groups(username, appname):
    fqan = username+'/app:'+appname
    groups=g.db.groupsInApp(g.currentuser,fqan)
    return jsonify({'groups':groups})


#######################################################################################################################

#######################################################################################################################
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__=='__main__':
    
    app.debug=True
    app.run()
