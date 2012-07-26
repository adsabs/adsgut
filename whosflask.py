from dbase import db_session, init_db
import whos
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, escape, make_response

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

@app.teardown_request
def shutdown_session(exception=None):
    g.db.remove()

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

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__=='__main__':
    app.debug=True
    app.run()
