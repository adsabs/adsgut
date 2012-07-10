#managing users, groups, and applications
import classes
import tbase
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
#What about adding user to default groups and all? I say routes. Dont muddy this.
OK=200
#RULE HERE: users are expected to be python objects. Anything else is a string

def validatespec(specdict, spectype):
    return specdict

class Whosdb(classes.Database):

    def addUser(currentuser, userspec):
        newuser=classes.User(validatespec(userspec, "user"))
        self.session.add(newuser)
        return OK

    def removeUser(currentuser, usertoberemovedemail):
        remuser=session.query(classes.User).filter_by(email=usertoberemovedemail)
        self.session.delete(remuser)
        return OK

    def createGroup(currentuser, groupspec):
        newgroup=classes.Group(validatespec(groupspec, "group"))
        self.session.add(newgroup)
        return OK

    def removeGroup(currentuser, fullyQualifiedGroupName):
        remgrp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remgrp)
        return OK


    #DERIVED

    #what about invitations. Is that taken over ny getting an oauth token in authspec?
    def addUserToGroup(currentuser, fullyQualifiedGroupName, usertobeaddded, authspec):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        usertobeadded.groupsin.append(grp)
        return OK

    def removeUserFromGroup(currentuser, fullyQualifiedGroupName, usertoberemoved):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        usertoberemoved.groupsin.remove(grp)
        return OK
        

    def changeOwnershipOfGroup(currentuser, fullyQualifiedGroupName, usertobenewowner):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        grp.owner = usertobenewowner
        return OK

    #INFORMATIONAL

    def usersInGroup(currentuser, fullyQualifiedGroupName):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        users=grp.groupusers
        return [e.info() for e in users]

    def groupsUserIsIn(currentuser, userwanted):
        groups=userwanted.groupsin
        return [e.info() for e in groups]

    #EVEN MORE DERIVED
    def addUserToApp(currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        app=self.session.query(classes.Application).filter_by(name=fullyQualifiedAppName)
        usertobeadded.applicationsin.append(app)
        return OK

    def removeUserFromApp(currentuser, fullyQualifiedAppName, usertoberemoved):
        app=self.session.query(classes.Application).filter_by(name=fullyQualifiedAppName)
        usertoberemoved.applicationsin.remove(app)
        return OK

    #How are these implemented: a route? And, what is this?
    def addGroupToApp(currentuser, fullyQualifiedAppName, fullyQualifiedGroupName, authspec):
        app=self.session.query(classes.Application).filter_by(name=fullyQualifiedAppName)
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        grp.applicationsin.append(app)
        #pubsub must add the individual users
        return OK

    def removeGroupFromApp(currentuser, fullyQualifiedAppName, fullyQualifiedGroupName):
        app=self.session.query(classes.Application).filter_by(name=fullyQualifiedAppName)
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        grp.applicationsin.remove(app)
        #pubsub depending on what we want to do to delete
        return OK


    def usersInApp(currentuser, fullyQualifiedAppName):
        app=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        users=app.applicationusers
        return [e.info() for e in users]

    def groupsInApp(currentuser, fullyQualifiedAppName):
        app=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        groups=app.applicationgroups
        return [e.info() for e in groups]

    def appsForUser(currentuser, userwanted):
        applications=userwanted.applicationsin
        return [e.info() for e in applications]

    def ownerOfGroups(currentuser, userwanted):
        groups=userwanted.groupsowned
        return [e.info() for e in groups]

    def ownerOfApps(currentuser, userwanted):
        applications=userwanted.appsowned
        return [e.info() for e in applications]



    

class TestA(tbase.TBase):

    def test_something(self):
        sess=self.session
        adsgutuser=classes.User(name='adsgut', email='adsgut@adslabs.org')
        adsuser=classes.User(name='ads', email='ads@adslabs.org')
        sess.add(adsgutuser)
        sess.add(adsuser)
        sess.flush() 