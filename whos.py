#managing users, groups, and applications
import classes
import tbase
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
#What about adding user to default groups and all? I say routes. Dont muddy this.

#RULE HERE: users are expected to be python objects. Anything else is a string

def validatespec(specdict, spectype):
    return specdict

class Whosdb(classes.Database):

    def addUser(currentuser, userspec):
        newuser=classes.User(validatespec(userspec, "user"))
        self.session.add(newuser)

    def removeUser(currentuser, usertoberemovedemail):
        remuser=session.query(classes.User).filter_by(email=usertoberemovedemail)
        self.session.delete(remuser)

    def createGroup(currentuser, groupspec):
        newgroup=classes.Group(validatespec(groupspec, "group"))
        self.session.add(newgroup)

    def removeGroup(currentuser, fullyQualifiedGroupName):
        remgrp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        #How will the cascades work? removing users? should we not archive?
        #from an ORM perspective its like groups should be added to a new table ArchivedGroup,
        #or perhaps just flagged "archived"
        self.session.delete(remgrp)


    #DERIVED

    #what about invitations. Is that taken over ny getting an oauth token in authspec?
    def addUserToGroup(currentuser, fullyQualifiedGroupName, usertobeaddded, authspec):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        usertobeadded.groupsin.append(grp)

    def removeUserFromGroup(currentuser, fullyQualifiedGroupName, usertoberemoved):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        usertoberemoved.groupsin.remove(grp)
        

    def changeOwnershipOfGroup(currentuser, fullyQualifiedGroupName, usertobenewowner):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        grp.owner = usertobenewowner

    #INFORMATIONAL

    def usersInGroup(currentuser, fullyQualifiedGroupName):
        pass

    def groupsUserIsIn(currentuser, userwanted):
        pass

    #EVEN MORE DERIVED
    def addUserToApp(currentuser, fullyQualifiedAppName, usertobeadded, authspec):
        pass

    def removeUserFromApp(currentuser, fullyQualifiedAppName, usertoberemoved):
        pass

    #How are these implemented: a route? And, what is this?
    def addGroupToApp(currentuser, fullyQualifiedAppName, fullyQualifiedGroupName, authspec):
        pass

    def removeGroupFromApp(currentuser, fullyQualifiedAppName, fullyQualifiedGroupName):
        pass


    def usersInApp(currentuser, fullyQualifiedAppName):
        pass

    def appsForUser(currentuser, userwanted):
        pass

    def ownerOfGroups(currentuser, userwanted):
        pass

    def ownerOfApps(currentuser, userwanted):
        pass



    

class TestA(tbase.TBase):

    def test_something(self):
        sess=self.session
        adsgutuser=classes.User(name='adsgut', email='adsgut@adslabs.org')
        adsuser=classes.User(name='ads', email='ads@adslabs.org')
        sess.add(adsgutuser)
        sess.add(adsuser)
        sess.flush() 