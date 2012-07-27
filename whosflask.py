from dbase import db_session, init_db
import whos
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, escape, make_response, jsonify

def initialize_application():
    init_db()
    currentuser=None
    whosdb=whos.Whosdb(db_session)
    adsgutuser=whosdb.addUser(currentuser, dict(nick='adsgut', email='adsgut@adslabs.org'))
    currentuser=adsgutuser
    adsgutdefault=whosdb.addGroup(currentuser, dict(name='default', creator=adsgutuser))
    public=whosdb.addGroup(currentuser, dict(name='public', creator=adsgutuser))
    whosdb.commit()
    #adsgutuser=User(name='adsgut', email='adsgut@adslabs.org')
    adsuser=whosdb.addUser(currentuser, dict(nick='ads', email='ads@adslabs.org'))
    adsdefault=whosdb.addGroup(currentuser, dict(name='default', creator=adsuser))
    #adsuser=User(name='ads', email='ads@adslabs.org')
    whosdb.commit()
    
    adspubsapp=whosdb.addApp(currentuser, dict(name='publications', creator=adsuser))
    whosdb.commit()

    rahuldave=whosdb.addUser(currentuser, dict(nick='rahuldave', email="rahuldave@gmail.com"))
    whosdb.addUserToGroup(currentuser, 'adsgut/public', rahuldave, None)
    #rahuldave.groupsin.append(public)
    rahuldavedefault=whosdb.addGroup(currentuser, dict(name='default', creator=rahuldave))
    rahuldave.groupsin.append(rahuldavedefault)
    whosdb.addUserToApp(currentuser, 'ads/publications', rahuldave, None)
    #rahuldave.applicationsin.append(adspubsapp)

    mlg=whosdb.addGroup(currentuser, dict(name='ml', creator=rahuldave))
    rahuldave.groupsin.append(mlg)
    whosdb.commit()
    jayluker=whosdb.addUser(currentuser, dict(nick='jayluker', email="jluker@gmail.com"))
    whosdb.addUserToGroup(currentuser, 'adsgut/public', jayluker, None)
    #jayluker.groupsin.append(public)
    jaylukerdefault=whosdb.addGroup(currentuser, dict(name='default', creator=jayluker))
    jayluker.groupsin.append(jaylukerdefault)
    whosdb.addUserToApp(currentuser, 'ads/publications', jayluker, None)
    #jayluker.applicationsin.append(adspubsapp)
    whosdb.commit()
    whosdb.inviteUserToGroup(currentuser, 'rahuldave/ml', jayluker, None)
    whosdb.commit()
    whosdb.acceptInviteToGroup(currentuser, 'rahuldave/ml', jayluker, None)
    whosdb.addGroupToApp(currentuser, 'ads/publications', 'adsgut/public', None )
    #public.applicationsin.append(adspubsapp)
    rahuldavedefault.applicationsin.append(adspubsapp)
    whosdb.commit()

app = Flask(__name__)



@app.before_request
def before_request():
        g.db=whos.Whosdb(db_session)
        if session.has_key('username'):
            g.currentuser=g.db.getUserForNick(session.username)
        else:
            g.currentuser=None

@app.teardown_request
def shutdown_session(exception=None):
    #g.db.commit()
    g.db.remove()

#EXPLICITLY COMMIT ON POSTS. THOUGH TO DO MULTIPLE THINGS, WE MAY WANT TO 
#SCHEDULE COMMITS SEPARATELY..really commits not a property of whosdb
@app.route('/')
def index():
    start='<a href="/login">Login</a><br/>'
    return render_template('index.html', users=g.db.allUsers(None))

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

#use this for op based POSTS?
#currentuser=g.db.getCurrentuser(session.username)
#GET for info
@app.route('/user/<nick>')
def douser(nick):
    userinfo=g.db.getUserInfo(nick)
    return jsonify(**userinfo)

@app.route('/user/<nick>/profile/html')
def profile(nick):
    pass

@app.route('/user/<nick>/groupsin')
def groupsin(nick):
    user=g.db.getUserForNick(nick)
    groups=g.db.groupsForUser(g.currentuser, user)
    return jsonify({'groups':groups})

@app.route('/user/<nick>/groupsowned')
def groupsowned(nick):
    user=g.db.getUserForNick(nick)
    groups=g.db.ownerOfGroups(g.currentuser, user)
    return jsonify({'groups':groups})

@app.route('/user/<nick>/groupsinvited')
def groupsinvited(nick):
    user=g.db.getUserForNick(nick)
    groups=g.db.groupInvitationsForUser(g.currentuser, user)
    return jsonify({'groups':groups})

@app.route('/user/<nick>/appsin')
def appsin(nick):
    user=g.db.getUserForNick(nick)
    apps=g.db.appsForUser(g.currentuser, user)
    return jsonify({'apps':apps})

@app.route('/user/<nick>/appsowned')
def appsowned(nick):
    user=g.db.getUserForNick(nick)
    apps=g.db.ownerOfApps(g.currentuser, user)
    return jsonify({'apps':apps})

#use this for the email invitation?
@app.route('/user/<nick>/appsinvited')
def appsinvited(nick):
    user=g.db.getUserForNick(nick)
    apps=g.db.appInvitationsForUser(g.currentuser, user)
    return jsonify({'apps':apps})

@app.route('/group/html')
def creategroup():
    pass

#get group info
@app.route('/group/<username>/<groupname>')
def dogroup(username, groupname):
    fqgn = username+'/'+groupname
    pass

@app.route('/group/<username>/<groupname>/profile/html')
def group_profile(username, groupname):
    fqgn = username+'/'+groupname
    pass

@app.route('/group/<username>/<groupname>/users')
def group_users(username, groupname):
    fqgn = username+'/'+groupname
    users=g.db.usersInGroup(g.currentuser,fqgn)
    return jsonify({'users':users})

@app.route('/app/html')
def createapp():
    pass

@app.route('/app/<username>/<appname>')
def doapp(username, appname):
    fqan = username+'/'+appname
    pass

@app.route('/app/<username>/<appname>/profile/html')
def app_profile(username, appname):
    pass

@app.route('/app/<username>/<appname>/users')
def application_users(username, appname):
    fqan = username+'/'+appname
    users=g.db.usersInApp(g.currentuser,fqan)
    return jsonify({'users':users})


@app.route('/app/<username>/<appname>/groups')
def application_groups(username, appname):
    fqan = username+'/'+appname
    groups=g.db.groupsInApp(g.currentuser,fqan)
    return jsonify({'groups':groups})

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__=='__main__':
    app.debug=True
    app.run()
