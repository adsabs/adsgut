#managing users, groups, and applications
from classes import *
import tbase
import dbase
import config
from permissions import permit
from errors import abort, doabort, ERRGUT
import types

OK=200
#RULE HERE: users are expected to be python objects. Anything else is a string
def is_stringtype(v):
    if type(v)==types.StringType or type(v)==types.UnicodeType:
        return True
    else:
        return False

# **Notes**
# 1. We are not protecting session adds and deletes with exceptions. What does this mean?
# 2. We are not worrying about cascade deletion, or much about deletion in general presently (BUG)
# 3. Some group addition will happen through routes. Not yet.
# 4. We must add a function for users to attach nicknames.

MUSTHAVEKEYS={
    'user':['email', 'nick'],
    'group':['creator', 'name'],
    'app':['creator', 'name']
}

#Validate spec for users, groups, and apps
def validatespec(specdict, spectype="user"):
    keysneeded=MUSTHAVEKEYS[spectype]
    keyswehave=specdict.keys()
    for k in keysneeded:
        if k not in keyswehave:
            doabort('BAD_REQ', "Key %s not in spec for %s" % (k, spectype))
    if spectype=='group' or spectype=='app':
        specdict['owner']=specdict['creator']
        specdict['fqin']=specdict['creator'].nick+"/"+spectype+":"+specdict['name']
    return specdict

#An interface to the user, groups, and apps database
class Whosdb(dbase.Database):

    #Get user object for nickname nick

    def isSystemUser(self, currentuser):
        if currentuser.nick=='adsgut':
            return True
        else:
            return False

    def getUserForNick(self, currentuser, nick):
        try:
            user=self.session.query(User).filter_by(nick=nick).one()
        except:
            doabort('NOT_FND', "User %s not found" % nick)
        return user

    #Get user info for nickname nick
    def getUserInfo(self, currentuser, userwantednick):
        user=self.getUserForNick(currentuser, userwantednick)
        permit(currentuser==user or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        return user.info()

    #Get group object given fqgn
    def getGroup(self, currentuser, fullyQualifiedGroupName):
        try:
            group=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        except:
            doabort('NOT_FND', "Group %s not found" % fullyQualifiedGroupName)
        return group

    #Get group info given fqgn
    def getGroupInfo(self, currentuser, fullyQualifiedGroupName):
        group=self.getGroup(currentuser, fullyQualifiedGroupName)
        return group.info()

    #Get app object fiven fqan
    def getApp(self, currentuser, fullyQualifiedAppName):
        try:
            app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        except:
            doabort('NOT_FND', "App %s not found" % fullyQualifiedAppName)
        return app

    #Get app info given fqan
    def getAppInfo(self, currentuser, fullyQualifiedAppName):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        return app.info()

    #Add user to system, given a userspec from flask user object. commit needed
    #This should never be called from the web interface, but can be called on the fly when user
    #logs in in Giovanni's system. So will there be a cookie or not?
    def addUser(self, currentuser, userspec):
        #permit(self.isSystemUser(currentuser), "Only System User can add users")
        vspec=validatespec(userspec, "user")
        #print vspec
        try:
            newuser=User(**vspec)
            self.session.add(newuser)
        except:
            doabort('BAD_REQ', "Failed adding user %s" % userspec['nick'])
        #Also add user to private default group and public group
        self.addGroup(currentuser, dict(name='default', creator=newuser, personalgroup=True))
        if newuser.nick == 'adsgut':
            #Shouldnt this be part of system configuration
            newuser.systemuser=True          
            self.addGroup(currentuser, dict(name='public', description="Public Items", creator=newuser))
        else:
            self.addUserToGroup(currentuser, 'adsgut/group:public', newuser, None)
        return newuser

    #BUG: we want to blacklist users and relist them
    #currently only allow users to be removed through scripts
    def removeUser(self, currentuser, usertoberemovednick):
        permit(self.isSystemUser(currentuser), "Only System User can remove users")
        remuser=self.getUserForNick(currentuser, usertoberemovednick)
        self.session.delete(remuser)
        return OK

    def addGroup(self, currentuser, groupspec):
        vspec=validatespec(groupspec, "group")
        try:
            newgroup=Group(**vspec)
        except:
            doabort('BAD_REQ', "Failed adding group %s" % groupspec['name'])
        #Also add user to private default group and public group
        self.session.add(newgroup)
        #self.commit()#needed as in addUserToGroup you do a full lookup. fix this!
        #print newgroup.fqin, newgroup.creator.info(), '<<<<<<'
        self.addUserToGroup(currentuser, newgroup, newgroup.creator, None)
        return newgroup

    def isOwnerOfGroup(self, currentuser, grp):
        if currentuser==grp.owner:
            return True
        else:
            return False

    def isMemberOfGroup(self, currentuser, grp):
        if currentuser in grp.groupusers:
            return True
        else:
            return False

    def isInvitedToGroup(self, currentuser, grp):
        if grp in currentuser.groupsinvitedto:
            return True
        else:
            return False

    def isOwnerOfApp(self, currentuser, app):
        if currentuser==app.owner:
            return True
        else:
            return False

    def isMemberOfApp(self, currentuser, app):
        if currentuser in app.appusers:
            return True
        else:
            return False

    def isInvitedToApp(self, currentuser, grp):
        if app in currentuser.applicationsinvitedto:
            return True
        else:
            return False
    
    #The only person who can remove a group is the system user or the owner
    def removeGroup(self,currentuser, fullyQualifiedGroupName):
        remgrp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isOwnerOfGroup(currentuser, remgrp) or self.isSystemUser(currentuser),
                "Only owner of group %s or systemuser can remove group" % remgrp.fqin)
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remgrp)
        return OK

    def addApp(self, currentuser, appspec):
        appspec=validatespec(appspec, "app")
        appspec['appgroup']=True
        try:
            newapp=Application(**appspec)
        except:
            doabort('BAD_REQ', "Failed adding app %s" % appspec['name'])  
        self.session.add(newapp)
        #self.commit()#needed due to full lookup in addUserToApp. fixthis
        self.addUserToApp(currentuser, newapp, newapp.creator, None)
        return newapp

    def removeApp(self,currentuser, fullyQualifiedAppName):
        remapp=self.getApp(currentuser, fullyQualifiedAppName)
        permit(self.isOwnerOfApp(currentuser, remapp) or self.isSystemUser(currentuser),
                "Only owner of app %s or systemuser can remove app" % remapp.fqin)
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remapp)
        return OK


    #DERIVED

    #adduser to group is direct. It cant be done for regular groups except in some circumstances
    #these are adding to default private group, and public group. Users must accept invites otherwise.
    #How do we do this in permits?
    def addUserToGroup(self, currentuser, grouporfullyQualifiedGroupName, usertobeadded, authspec):
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName

        try:
            usertobeadded.groupsin.append(grp)
        except:
            doabort('BAD_REQ', "Failed adding user %s to group %s" % (usertobeadded.nick, grp.fqin))
        return OK

    def inviteUserToGroup(self, currentuser, fullyQualifiedGroupName, usertobeadded, authspec):
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isOwnerOfGroup(currentuser, grp), " User %s must be owner of group %s" % (currentuser.nick, grp.fqin))
        try:
            usertobeadded.groupsinvitedto.append(grp)
        except:
            doabort('BAD_REQ', "Failed inviting user %s to group %s" % (usertobeadded.nick, grp.fqin))
        return OK

    def acceptInviteToGroup(self, currentuser, fullyQualifiedGroupName, authspec):
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isInvitedToGroup(currentuser, grp), " User %s must be invited to group %s" % (currentuser.nick, grp.fqin))
        try:
            currentuser.groupsin.append(grp)
        except:
            doabort('BAD_REQ', "Failed in user %s accepting invite to group %s" % (currentuser.nick, grp.fqin))
        return OK

    def removeUserFromGroup(self, currentuser, fullyQualifiedGroupName, usertoberemoved):
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isOwnerOfGroup(currentuser, grp), " User %s must be owner of group %s" % (currentuser.nick, grp.fqin))
        try:
            usertoberemoved.groupsin.remove(grp)
        except:
            doabort('BAD_REQ', "Failed removing user %s from group %s" % (usertoberemoved.nick, grp.fqin))
        return OK
        
    #BUG: shouldnt new owner have to accept this. Currently, no. We foist it. We'll perhaps never expose this.
    def changeOwnershipOfGroup(self, currentuser, fullyQualifiedGroupName, usertobenewowner):
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isOwnerOfGroup(currentuser, grp), " User %s must be owner of group %s" % (currentuser.nick, grp.fqin))
        try:
            oldownernick=grp.owner.nick
            grp.owner = usertobenewowner
        except:
            doabort('BAD_REQ', "Failed changing owner from %s to %s for group %s" % (oldownernick, usertobenewowner.nick, grp.fqin))    
        return OK


    #EVEN MORE DERIVED
    #who runs this? is it run on acceptance of group to app? How to permit for that?
    def addUserToApp(self, currentuser, apporfullyQualifiedAppName, usertobeadded, authspec):
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        
        try:
            usertobeadded.applicationsin.append(app)
        except:
            doabort('BAD_REQ', "Failed adding user %s to app %s" % (usertobeadded.nick, app.fqin))
        return OK

    #and who runs this?
    def inviteUserToApp(self, currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        permit(self.isOwnerOfApp(currentuser, app), " User %s must be owner of app %s" % (currentuser.nick, app.fqin))
        try:
            usertobeadded.applicationsinvitedto.append(app)
        except:
            doabort('BAD_REQ', "Failed inviting user %s to app %s" % (usertobeadded.nick, app.fqin))
        return OK

    def acceptInviteToApp(self, currentuser, fullyQualifiedAppName, authspec):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        permit(self.isInvitedToApp(currentuser, app), " User %s must be invited to app %s" % (currentuser.nick, app.fqin))
        try:
            currentuser.applicationsin.append(app)
        except:
            doabort('BAD_REQ', "Failed in user %s accepting invite to app %s" % (currentuser.nick, app.fqin))
        return OK

    def removeUserFromApp(self, currentuser, fullyQualifiedAppName, usertoberemoved):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        permit(self.isOwnerOfApp(currentuser, app), " User %s must be owner of app %s" % (currentuser.nick, app.fqin))
        try:
            usertoberemoved.applicationsin.remove(app)
        except:
            doabort('BAD_REQ', "Failed removing user %s from app %s" % (usertoberemoved.nick, app.fqin))
        return OK

    #How are these implemented: a route? And, what is this?
    def addGroupToApp(self, currentuser, fullyQualifiedAppName, fullyQualifiedGroupName, authspec):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        #You must be owner of the group and member of the app
        permit(self.isOwnerOfGroup(currentuser, grp), " User %s must be owner of group %s" % (currentuser.nick, grp.fqin))
        permit(self.isMemberOfApp(currentuser, app), " User %s must be member of app %s" % (currentuser.nick, app.fqin))
        try:
            grp.applicationsin.append(app)
            #pubsub must add the individual users. BUG is that how we want to do it?
        except:
            doabort('BAD_REQ', "Failed adding group %s to app %s" % (grp.fqin, app.fqin))
        return OK

    def removeGroupFromApp(self, currentuser, fullyQualifiedAppName, fullyQualifiedGroupName):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isOwnerOfGroup(currentuser, grp), " User %s must be owner of group %s" % (currentuser.nick, grp.fqin))
        permit(self.isMemberOfApp(currentuser, app), " User %s must be member of app %s" % (currentuser.nick, app.fqin))
        try:
            grp.applicationsin.remove(app)
            #pubsub depending on what we want to do to delete
        except:
            doabort('BAD_REQ', "Failed removing group %s from app %s" % (grp.fqin, app.fqin))
        return OK


    #INFORMATIONAL: no aborts for these informationals as just queries that could returm empty.

    def allUsers(self, currentuser):
        permit(self.isSystemUser(currentuser), "Only System User allowed")
        users=self.session.query(User).filter_by(systemuser=False).all()
        return [e.info() for e in users]

    def allGroups(self, currentuser):
        permit(self.isSystemUser(currentuser), "Only System User allowed")
        groups=self.session.query(Group).filter_by(appgroup=False, personalgroup=False).all()
        return [e.info() for e in groups]

    def allApps(self, currentuser):
        permit(self.isSystemUser(currentuser), "Only System User allowed")
        apps=self.session.query(Application).filter_by(appgroup=True).all()
        return [e.info() for e in apps]


    def ownerOfGroups(self, currentuser, userwanted):
        permit(currentuser==userwanted or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        groups=userwanted.groupsowned
        #print "GROUPS", groups
        return [e.info() for e in groups]

    def ownerOfApps(self, currentuser, userwanted):
        permit(currentuser==userwanted or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        applications=userwanted.appsowned
        return [e.info() for e in applications]


    def usersInGroup(self, currentuser, fullyQualifiedGroupName):
        grp=self.getGroup(currentuser, fullyQualifiedGroupName)
        permit(self.isMemberOfGroup(currentuser, grp) or self.isSystemUser(currentuser), 
            "Only member of group %s or systemuser can get users" % (currentuser.nick, grp.fqin))
        users=grp.groupusers
        return [e.info() for e in users]

    def groupsForUser(self, currentuser, userwanted):
        permit(currentuser==userwanted or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        groups=userwanted.groupsin
        return [e.info() for e in groups]

    def groupInvitationsForUser(self, currentuser, userwanted):
        permit(currentuser==userwanted or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        groups=userwanted.groupsinvitedto
        return [e.info() for e in groups]

    def usersInApp(self, currentuser, fullyQualifiedAppName):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        permit(self.isMemberOfApp(currentuser, app) or self.isSystemUser(currentuser),
                "Only member of app %s or systemuser can get users" % remapp.fqin)
        users=app.applicationusers
        return [e.info() for e in users]

    def groupsInApp(self, currentuser, fullyQualifiedAppName):
        app=self.getApp(currentuser, fullyQualifiedAppName)
        permit(self.isOwnerOfApp(currentuser, app) or self.isSystemUser(currentuser),
                "Only owner of app %s or systemuser can get groups" % remapp.fqin)
        groups=app.applicationgroups
        return [e.info() for e in groups]

    def appsForUser(self, currentuser, userwanted):
        permit(currentuser==userwanted or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        applications=userwanted.applicationsin
        return [e.info() for e in applications]

    def appInvitationsForUser(self, currentuser, userwanted):
        permit(currentuser==userwanted or self.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        apps=userwanted.applicationsinvitedto
        return [e.info() for e in apps]
#why cant arguments be specified via destructuring as in coffeescript
    
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
    print "ending init"

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