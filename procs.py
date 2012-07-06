#being a file of procs that allow for addition, deletion, and mods of stuff
#should no all functions operate on vectors of items
import classes
import tbase
#FUNDAMENTAL--post multiple times to change itemspec

class GutDb(classes.Database):


    def postItemToGroup(self, currentuser, group, itemjson):
    	pass #return itemuri

    def postTagItemToGroup(self, currentuser, group, itemuri, tagtype, tagtext):
    	pass #return taguri

    def getItemsForUser(self, currentuser, wanteduser, itemtypespec):
    	pass #[itemuri]

    def editItem(self, currentuser, itemuri, itemnewjson):
    	pass

    def editTagItem(self, currentuser, taguri, tagtype, tagtext):
    	pass# return taguri


    #DERIVED
    def tagItem(self, currentuser, itemuri, tagtype, tagtext, tagspec):
    	pass#return taguri

    def saveItem(self, currentuser, itemjson):
    	"posts to self group" #return taguri

    def changeTagspec(self, currentuser, itemuri, taguri, newtagspec):
    	pass

    def getTagsForItems(self, currentuser, itemurilist, tagtypespec):
    	pass #return [itemuri, taguri]

    def getTagsForTypespec(self, currentuser, tagtypespec):
    	pass #return [itemuri, taguri]

    def getItemsForGroup(self, currentuser, wantedgroup, itemtypespec):
    	pass #[itemuri]

    def getItemsForApp(self, currentuser, wantedapp, itemtypespec):
    	pass #[itemuri]

    def getItemsForGroupAndApp(self, currentuser, wanteduser, wantedgroup, itemtypespec):
    	pass #[itemuri]

    def getItemsForUserAndApp(self, currentuser, wanteduser, wantedapp, itemtypespec):
    	pass #[itemuri]

#conbine get tags for items and get items for self, currentuser and app to get tags for self, currentusers and apps
