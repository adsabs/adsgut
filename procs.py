#being a file of procs that allow for addition, deletion, and mods of stuff
#should no all functions operate on vectors of items

#FUNDAMENTAL--post multiple times to change itemspec
def postItemToGroup(user, group, itemjson):
	pass #return itemuri

def postTagItemToGroup(user, group, itemuri, tagtype, tagtext):
	pass #return taguri

def getItemsForUser(user, wanteduser, itemtypespec):
	pass #[itemuri]

def editItem(user, itemuri, itemnewjson):
	pass

def editTagItem(user, taguri, tagtype, tagtext):
	pass# return taguri


#DERIVED
def tagItem(user, itemuri, tagtype, tagtext, tagspec):
	pass#return taguri

def saveItem(user, itemjson):
	"posts to self group" #return taguri

def changeTagspec(user, itemuri, taguri, newtagspec):
	pass

def getTagsForItems(user, itemurilist, tagtypespec):
	pass #return [itemuri, taguri]

def getTagsForTypespec(user, tagtypespec):
	pass #return [itemuri, taguri]

def getItemsForGroup(user, wantedgroup, itemtypespec):
	pass #[itemuri]

def getItemsForApp(user, wantedapp, itemtypespec):
	pass #[itemuri]

def getItemsForGroupAndApp(user, wanteduser, wantedgroup, itemtypespec):
	pass #[itemuri]

def getItemsForUserAndApp(user, wanteduser, wantedapp, itemtypespec):
	pass #[itemuri]

#conbine get tags for items and get items for user and app to get tags for users and apps