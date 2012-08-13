from flaskrunner import app, g
@app.route('/poal')
def poal():
    return render_template('poal.html', users=g.db.allUsers(g.currentuser), 
        groups=g.db.allGroups(g.currentuser), apps=g.db.allApps(g.currentuser))
