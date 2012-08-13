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


from poalflask import *

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__=='__main__':
    app.debug=True
    app.run()