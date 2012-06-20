#managing users, groups, and applications
import classes
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions?
#FUNDAMENTAL
def addUser(session, currentuser, userspec):
	newuser=classes.User(userspec)
	session.add(newuser)

def removeUser(session, currentuser, usertoberemovedemail):
	remuser=session.query(classes.User).filter_by(email=usertoberemovedemail)
	session.delete(remuser)

def createGroup(session, currentuser, groupspec):
	newuser=classes.Group(groupspec)
	session.add(newuser)

def removeGroup(session, currentuser, fqgn):
	remgrp=session.query(classes.Group).filter_by(name=fqgn)
	session.delete(remgrp)


#DERIVED

#what about invitations. Is that taken over ny getting an oauth token in authspec?
def addUserToGroup(session, currentuser, group, usertobeaddded, authspec):
	pass

def removeUserFromGroup(session, currentuser, group, usertoberemoved):
	pass

def changeOwnershipOfGroup(session, currentuser, group, usertobenewowner):
	pass

#INFORMATIONAL

def usersInGroup(session, currentuser, group):
	pass

def groupsUserIsIn(session, currentuser, userwanted):
	pass

#EVEN MORE DERIVED
def addUserToApp(session, currentuser, app, usertobeadded, authspec):
	pass

def removeUserFromApp(session, currentuser, app, usertoberemoved):
	pass

#How are these implemented: a route? And, what is this?
def addGroupToApp(session, currentuser, app, grouptoadd, authspec):
	pass

def removeGroupFromApp(session, currentuser, app, grouptoremove):
	pass


def usersInApp(session, currentuser, app):
	pass

def appsForUser(session, currentuser, userwanted):
	pass

def ownerOfGroups(session, currentuser, userwanted):
	pass

def ownerOfApps(session, currentuser, userwanted):
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