#managing users, groups, and applications
from classes import *
import tbase
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
#What about adding user to default groups and all? I say routes. Dont muddy this.
OK=200
#RULE HERE: users are expected to be python objects. Anything else is a string


#NEXT: respect fully qualifieds all through app, figure what to do about use instances at this level NEXT

def validatespec(specdict, spectype):
    return specdict

class Whosdb(Database):

    def addUser(self, currentuser, userspec):
        vspec=validatespec(userspec, "user")
        #print vspec
        newuser=User(**vspec)
        self.session.add(newuser)
        return newuser

    def removeUser(self, currentuser, usertoberemovedemail):
        remuser=session.query(User).filter_by(email=usertoberemovedemail)
        self.session.delete(remuser)
        return OK

    def addGroup(self, currentuser, groupspec):
        newgroup=Group(**validatespec(groupspec, "group"))
        self.session.add(newgroup)
        return newgroup

    def removeGroup(self,currentuser, fullyQualifiedGroupName):
        remgrp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remgrp)
        return OK

    def addApp(self, currentuser, appspec):
        newapp=Application(**validatespec(appspec, "app"))
        self.session.add(newapp)
        return newapp

    def removeApp(self,currentuser, fullyQualifiedAppName):
        remapp=self.session.query(Application).filter_by(name=fullyQualifiedAppName)
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remapp)
        return OK


    #DERIVED

    #what about invitations. Is that taken over ny getting an oauth token in authspec?
    def addUserToGroup(self, currentuser, fullyQualifiedGroupName, usertobeadded, authspec):
        grp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        usertobeadded.groupsin.append(grp[0])
        return OK

    def removeUserFromGroup(self, currentuser, fullyQualifiedGroupName, usertoberemoved):
        grp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        usertoberemoved.groupsin.remove(grp[0])
        return OK
        

    def changeOwnershipOfGroup(self, currentuser, fullyQualifiedGroupName, usertobenewowner):
        grp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        grp.owner = usertobenewowner
        return OK

    #INFORMATIONAL

    def allUsers(self, currentuser):
        users=self.session.query(User).all()
        return [e.info() for e in users]

    def allGroups(self, currentuser):
        users=self.session.query(Group).all()
        return [e.info() for e in users]

    def usersInGroup(self, currentuser, fullyQualifiedGroupName):
        grp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        users=grp[0].groupusers
        return [e.info() for e in users]

    def groupsUserIsIn(self, currentuser, userwanted):
        groups=userwanted.groupsin
        return [e.info() for e in groups]

    #EVEN MORE DERIVED
    def addUserToApp(self, currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        app=self.session.query(Application).filter_by(name=fullyQualifiedAppName)
        usertobeadded.applicationsin.append(app[0])
        return OK

    def removeUserFromApp(self, currentuser, fullyQualifiedAppName, usertoberemoved):
        app=self.session.query(Application).filter_by(name=fullyQualifiedAppName)
        usertoberemoved.applicationsin.remove(app[0])
        return OK

    #How are these implemented: a route? And, what is this?
    def addGroupToApp(self, currentuser, fullyQualifiedAppName, fullyQualifiedGroupName, authspec):
        app=self.session.query(Application).filter_by(name=fullyQualifiedAppName)
        grp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        grp[0].applicationsin.append(app[0])
        #pubsub must add the individual users
        return OK

    def removeGroupFromApp(self, currentuser, fullyQualifiedAppName, fullyQualifiedGroupName):
        app=self.session.query(Application).filter_by(name=fullyQualifiedAppName)
        grp=self.session.query(Group).filter_by(name=fullyQualifiedGroupName)
        grp[0].applicationsin.remove(app[0])
        #pubsub depending on what we want to do to delete
        return OK


    def usersInApp(self, currentuser, fullyQualifiedAppName):
        app=self.session.query(Group).filter_by(name=fullyQualifiedAppName)
        users=app[0].applicationusers
        return [e.info() for e in users]

    def groupsInApp(self, currentuser, fullyQualifiedAppName):
        app=self.session.query(Application).filter_by(name=fullyQualifiedAppName)
        groups=app[0].applicationgroups
        return [e.info() for e in groups]

    def appsForUser(self, currentuser, userwanted):
        applications=userwanted.applicationsin
        return [e.info() for e in applications]

    def ownerOfGroups(self, currentuser, userwanted):
        groups=userwanted.groupsowned
        return [e.info() for e in groups]

    def ownerOfApps(self, currentuser, userwanted):
        applications=userwanted.appsowned
        return [e.info() for e in applications]


#BUG: why cant arguments be specified via destructuring as in coffeescript
    

class TestA(tbase.TBase):

    def test_something(self):
        print "HELLO"
        sess=self.session
        currentuser=None
        whosdb=Whosdb(sess)
        adsgutuser=whosdb.addUser(currentuser, dict(name='adsgut', email='adsgut@adslabs.org'))
        adsgutdefault=whosdb.addGroup(currentuser, dict(name='default', owner=adsgutuser))
        public=whosdb.addGroup(currentuser, dict(name='public', owner=adsgutuser))
        whosdb.commit()
        #adsgutuser=User(name='adsgut', email='adsgut@adslabs.org')
        adsuser=whosdb.addUser(currentuser, dict(name='ads', email='ads@adslabs.org'))
        adsdefault=whosdb.addGroup(currentuser, dict(name='default', owner=adsuser))
        #adsuser=User(name='ads', email='ads@adslabs.org')
        whosdb.commit()
        
        adspubsapp=whosdb.addApp(currentuser, dict(name='publications', owner=adsuser))
        whosdb.commit()

        rahuldave=whosdb.addUser(currentuser, dict(name='rahuldave', email="rahuldave@gmail.com"))
        whosdb.addUserToGroup(currentuser, 'public', rahuldave, None)
        #rahuldave.groupsin.append(public)
        rahuldavedefault=whosdb.addGroup(currentuser, dict(name='default', owner=rahuldave))
        rahuldave.groupsin.append(rahuldavedefault)
        whosdb.addUserToApp(currentuser, 'publications', rahuldave, None)
        #rahuldave.applicationsin.append(adspubsapp)
        whosdb.commit()
        jayluker=whosdb.addUser(currentuser, dict(name='jayluker', email="jluker@gmail.com"))
        whosdb.addUserToGroup(currentuser, 'public', jayluker, None)
        #jayluker.groupsin.append(public)
        jaylukerdefault=whosdb.addGroup(currentuser, dict(name='default', owner=jayluker))
        jayluker.groupsin.append(jaylukerdefault)
        whosdb.addUserToApp(currentuser, 'publications', jayluker, None)
        #jayluker.applicationsin.append(adspubsapp)
        whosdb.commit()
        whosdb.addGroupToApp(currentuser, 'publications', 'public', None )
        #public.applicationsin.append(adspubsapp)
        rahuldavedefault.applicationsin.append(adspubsapp)
        whosdb.commit()
        print whosdb.allUsers(currentuser)
        print whosdb.allGroups(currentuser)
        print whosdb.usersInGroup(currentuser, 'public')
        print whosdb.usersInApp(currentuser, 'publications')
        print whosdb.groupsInApp(currentuser, 'publications')
        print adspubsapp.applicationgroups.all()
        whosdb.edu()