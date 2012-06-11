#managing users, groups, and applications

#FUNDAMENTAL
def addUser(currentuser, userspec):
	pass

def removeUser(currentuser, usertoberemoved):
	pass

def createGroup(currentuser, group):
	pass

def removeGroup(currentuser, group):
	pass


#DERIVED

#what about invitations. Is that taken over ny getting an oauth token in authspec?
def addUserToGroup(currentuser, group, usertobeaddded, authspec):
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
