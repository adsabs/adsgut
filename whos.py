#managing users, groups, and applications
from classes import *
import tbase
import dbase
import config
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
#What about adding user to default groups and all? I say routes. Dont muddy this.
OK=200
#RULE HERE: users are expected to be python objects. Anything else is a string


#NEXT: respect fully qualifieds all through app, figure what to do about user instances at this level NEXT

def validatespec(specdict, spectype):
    if spectype=='group' or spectype=='app':
        specdict['owner']=specdict['creator']
        specdict['fqin']=specdict['creator'].nick+"/"+spectype+":"+specdict['name']
    return specdict

class Whosdb(dbase.Database):

    def getUserForNick(self, currentuser, nick):
        user=self.session.query(User).filter_by(nick=nick).one()
        return user

    def getUserInfo(self, currentuser, userwantednick):
        user=self.session.query(User).filter_by(nick=userwantednick).one()
        return user.info()

    def getGroupInfo(self, currentuser, fullyQualifiedGroupName):
        group=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        return group.info()

    def getAppInfo(self, currentuser, fullyQualifiedAppName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        return app.info()


    def addUser(self, currentuser, userspec):
        vspec=validatespec(userspec, "user")
        #print vspec
        newuser=User(**vspec)
        self.session.add(newuser)
        #Also add user to private default group and public group
        self.addGroup(currentuser, dict(name='default', creator=newuser, personalgroup=True))
        if newuser.nick == 'adsgut':
            newuser.systemuser=True          
            self.addGroup(currentuser, dict(name='public', description="Public Items", creator=newuser))
        else:
            self.addUserToGroup(currentuser, 'adsgut/group:public', newuser, None)
        return newuser

    def removeUser(self, currentuser, usertoberemovednick):
        remuser=session.query(User).filter_by(nick=usertoberemovednick).one()
        self.session.delete(remuser)
        return OK

    def addGroup(self, currentuser, groupspec):
        newgroup=Group(**validatespec(groupspec, "group"))
        self.session.add(newgroup)
        self.commit()#needed as in addUserToGroup you do a full lookup
        #print newgroup.fqin, newgroup.creator.info(), '<<<<<<'
        self.addUserToGroup(currentuser, newgroup.fqin, newgroup.creator, None)
        return newgroup

    def removeGroup(self,currentuser, fullyQualifiedGroupName):
        remgrp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remgrp)
        return OK

    def addApp(self, currentuser, appspec):
        appspec['appgroup']=True
        newapp=Application(**validatespec(appspec, "app"))
        self.session.add(newapp)
        self.commit()#needed due to full lookup in addUserToApp
        self.addUserToApp(currentuser, newapp.fqin, newapp.creator, None)
        return newapp

    def removeApp(self,currentuser, fullyQualifiedAppName):
        remapp=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remapp)
        return OK


    #DERIVED

    #what about invitations. Is that taken over ny getting an oauth token in authspec?
    def addUserToGroup(self, currentuser, fullyQualifiedGroupName, usertobeadded, authspec):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        usertobeadded.groupsin.append(grp)
        return OK

    def inviteUserToGroup(self, currentuser, fullyQualifiedGroupName, usertobeadded, authspec):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        usertobeadded.groupsinvitedto.append(grp)
        return OK

    def acceptInviteToGroup(self, currentuser, fullyQualifiedGroupName, usertobeadded, authspec):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        if grp in usertobeadded.groupsinvitedto:
            usertobeadded.groupsin.append(grp)
        return OK

    def removeUserFromGroup(self, currentuser, fullyQualifiedGroupName, usertoberemoved):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        usertoberemoved.groupsin.remove(grp)
        return OK
        

    def changeOwnershipOfGroup(self, currentuser, fullyQualifiedGroupName, usertobenewowner):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        grp.owner = usertobenewowner
        return OK

    #INFORMATIONAL

    def allUsers(self, currentuser):
        users=self.session.query(User).filter_by(systemuser=False).all()
        return [e.info() for e in users]

    def allGroups(self, currentuser):
        groups=self.session.query(Group).filter_by(appgroup=False, personalgroup=False).all()
        return [e.info() for e in groups]

    def allApps(self, currentuser):
        apps=self.session.query(Application).filter_by(appgroup=True).all()
        return [e.info() for e in apps]



    #EVEN MORE DERIVED
    #who runs this?
    def addUserToApp(self, currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        usertobeadded.applicationsin.append(app)
        return OK

    #and who runs this?
    def inviteUserToApp(self, currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        usertobeadded.applicationsinvitedto.append(app)
        return OK

    def acceptInviteToApp(self, currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        if app in usertobeadded.applicationsinvitedto:
            usertobeadded.applicationsin.append(app)
        return OK

    def removeUserFromApp(self, currentuser, fullyQualifiedAppName, usertoberemoved):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        usertoberemoved.applicationsin.remove(app)
        return OK

    #How are these implemented: a route? And, what is this?
    def addGroupToApp(self, currentuser, fullyQualifiedAppName, fullyQualifiedGroupName, authspec):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        grp.applicationsin.append(app)
        #pubsub must add the individual users
        return OK

    def removeGroupFromApp(self, currentuser, fullyQualifiedAppName, fullyQualifiedGroupName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        grp.applicationsin.remove(app)
        #pubsub depending on what we want to do to delete
        return OK


    def usersInApp(self, currentuser, fullyQualifiedAppName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        users=app.applicationusers
        return [e.info() for e in users]

    def groupsInApp(self, currentuser, fullyQualifiedAppName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        groups=app.applicationgroups
        return [e.info() for e in groups]

    def appsForUser(self, currentuser, userwanted):
        applications=userwanted.applicationsin
        return [e.info() for e in applications]

    def ownerOfGroups(self, currentuser, userwanted):
        groups=userwanted.groupsowned
        #print "GROUPS", groups
        return [e.info() for e in groups]

    def ownerOfApps(self, currentuser, userwanted):
        applications=userwanted.appsowned
        return [e.info() for e in applications]


    def usersInGroup(self, currentuser, fullyQualifiedGroupName):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        users=grp.groupusers
        return [e.info() for e in users]

    def groupsForUser(self, currentuser, userwanted):
        groups=userwanted.groupsin
        return [e.info() for e in groups]

    def groupInvitationsForUser(self, currentuser, userwanted):
        groups=userwanted.groupsinvitedto
        return [e.info() for e in groups]

    def appInvitationsForUser(self, currentuser, userwanted):
        apps=userwanted.applicationsinvitedto
        return [e.info() for e in apps]
#BUG: why cant arguments be specified via destructuring as in coffeescript
    
def initialize_application(db_session):
    currentuser=None
    whosdb=Whosdb(db_session)
    adsgutuser=whosdb.addUser(currentuser, dict(nick='adsgut', name="ADS GUT", email='adsgut@adslabs.org'))
    currentuser=adsgutuser
    whosdb.commit()
    #adsgutuser=User(name='adsgut', email='adsgut@adslabs.org')
    adsuser=whosdb.addUser(currentuser, dict(nick='ads', email='ads@adslabs.org'))
    #adsuser=User(name='ads', email='ads@adslabs.org')
    whosdb.commit()
    
    adspubsapp=whosdb.addApp(currentuser, dict(name='publications', description="ADS's flagship publication app", creator=adsuser))
    whosdb.commit()

    rahuldave=whosdb.addUser(currentuser, dict(nick='rahuldave', email="rahuldave@gmail.com"))
    whosdb.addUserToApp(currentuser, 'ads/app:publications', rahuldave, None)
    #rahuldave.applicationsin.append(adspubsapp)

    mlg=whosdb.addGroup(currentuser, dict(name='ml', description="Machine Learning Group", creator=rahuldave))
    whosdb.commit()
    jayluker=whosdb.addUser(currentuser, dict(nick='jayluker', email="jluker@gmail.com"))
    whosdb.addUserToApp(currentuser, 'ads/app:publications', jayluker, None)
    #jayluker.applicationsin.append(adspubsapp)
    whosdb.commit()
    whosdb.inviteUserToGroup(currentuser, 'rahuldave/group:ml', jayluker, None)
    whosdb.commit()
    whosdb.acceptInviteToGroup(currentuser, 'rahuldave/group:ml', jayluker, None)
    whosdb.addGroupToApp(currentuser, 'ads/app:publications', 'adsgut/group:public', None )
    #public.applicationsin.append(adspubsapp)
    #rahuldavedefault.applicationsin.append(adspubsapp)
    whosdb.commit()
    print "=====", mlg.appgroup, adspubsapp.appgroup

class TestA(tbase.TBase):

    def test_something(self):
        print "HELLO"
        sess=self.session
        currentuser=None
        whosdb=Whosdb(sess)
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
        print whosdb.allUsers(currentuser)
        print whosdb.allGroups(currentuser)#[this includes apps]
        print whosdb.usersInGroup(currentuser, 'adsgut/public')
        print whosdb.usersInGroup(currentuser, 'rahuldave/ml')
        print whosdb.usersInApp(currentuser, 'ads/publications')
        print whosdb.groupsInApp(currentuser, 'ads/publications')
        print adspubsapp.applicationgroups.all()
        print whosdb.groupsForUser(currentuser, rahuldave)
        whosdb.edu()

if __name__=="__main__":
    import os, os.path
    if os.path.exists(config.DBASE_FILE):
        os.remove(config.DBASE_FILE)
    engine, db_session = dbase.setup_db(config.DBASE_FILE)
    dbase.init_db(engine)
    initialize_application(db_session)