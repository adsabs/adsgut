#managing users, groups, and applications
import classes
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL

class Whosdb(object):

    def __init__(self, session):
        self.session = session

    def addUser(currentuser, userspec):
        newuser=classes.User(userspec)
        self.session.add(newuser)

    def removeUser(currentuser, usertoberemovedemail):
        remuser=session.query(classes.User).filter_by(email=usertoberemovedemail)
        self.session.delete(remuser)

    def createGroup(currentuser, groupspec):
        newuser=classes.Group(groupspec)
        self.session.add(newuser)

    def removeGroup(currentuser, fullyQualifiedGroupName):
        remgrp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        self.session.delete(remgrp)


    #DERIVED

    #what about invitations. Is that taken over ny getting an oauth token in authspec?
    def addUserToGroup(currentuser, fullyQualifiedGroupName, usertobeaddded, authspec):
        grp=self.session.query(classes.Group).filter_by(name=fullyQualifiedGroupName)
        pass

    def removeUserFromGroup(currentuser, group, usertoberemoved):
        pass

    def changeOwnershipOfGroup(currentuser, group, usertobenewowner):
        pass

    #INFORMATIONAL

    def usersInGroup(currentuser, group):
        pass

    def groupsUserIsIn(currentuser, userwanted):
        pass

    #EVEN MORE DERIVED
    def addUserToApp(currentuser, app, usertobeadded, authspec):
        pass

    def removeUserFromApp(currentuser, app, usertoberemoved):
        pass

    #How are these implemented: a route? And, what is this?
    def addGroupToApp(currentuser, app, grouptoadd, authspec):
        pass

    def removeGroupFromApp(currentuser, app, grouptoremove):
        pass


    def usersInApp(currentuser, app):
        pass

    def appsForUser(currentuser, userwanted):
        pass

    def ownerOfGroups(currentuser, userwanted):
        pass

    def ownerOfApps(currentuser, userwanted):
        pass

class TestClass1:   
    def setup(self):
        engine = create_engine('sqlite:///:memory:', echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        # You probably need to create some tables and 
        # load some test data, do so here.

        # To create tables, you typically do:
        DaBase.metadata.create_all(engine)

    def teardown(self):
        self.session.close()


    def test_something(self):
        sess=self.session
        adsgutuser=User(name='adsgut')
        adsuser=User(name='ads')
        sess.add(adsgutuser)
        sess.add(adsuser)
        sess.flush()