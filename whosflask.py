from dbase import setup_db
import whos
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, escape, make_response, jsonify


engine, db_session=setup_db("/tmp/adsgut.db")
app = Flask(__name__)



@app.before_request
def before_request():
        g.db=whos.Whosdb(db_session)
        if session.has_key('username'):
            g.currentuser=g.db.getUserForNick(None, session['username'])
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
    return render_template('index.html', users=g.db.allUsers(g.currentuser), 
        groups=g.db.allGroups(g.currentuser), apps=g.db.allApps(g.currentuser))

@app.route('/poal')
def poal():
    return render_template('poal.html', users=g.db.allUsers(g.currentuser), 
        groups=g.db.allGroups(g.currentuser), apps=g.db.allApps(g.currentuser))

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

#POST/GET
@app.route('/group/html')
def creategroup():
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
#POST/GET
@app.route('/app/html')
def createapp():
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

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__=='__main__':
    app.debug=True
    app.run()
