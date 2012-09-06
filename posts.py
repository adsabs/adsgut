from classes import *
from whos import Whosdb, initialize_application
import tbase
import dbase
import types
import config
from sqlalchemy.orm import join, aliased
from permissions import permit
from errors import abort, doabort
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
OK=200

#pubsub to be used in conjunction with the access table to get stuff into all groups.
#remember to have a proper exception mechanism
#BUG: Rrewrite this whole file TO UE JOINS SIMPLY

##Issues
# 1. its not clear how, or that we are enforcing uniqieness at many place, for.eg, nick/uri or nick/name
# 2. Add last updated to tag's and let apps and groups get this
# 3. Instead of doAbort using flask exceptions, it should use ours and we should just map to handle by http layer
# 4. BUG: shouldnt all lookups on currentuser really be on useras? fix this when doing permits

MUSTHAVEKEYS={
    'item':['creator', 'name', 'itemtype'],
    'tag':['creator', 'name', 'tagtype'],
    'itemtype':['creator', 'name'],
    'tagtype':['creator', 'name']
}

def validatespec(specdict, spectype="item"):
    keysneeded=MUSTHAVEKEYS[spectype]
    keyswehave=specdict.keys()
    for k in keysneeded:
        if k not in keyswehave:
            doabort('BAD_REQ', "Key %s not in spec for %s" % (k, spectype))
    if spectype=="tag":
        specdict['fqin']=specdict['creator'].nick+"/"+specdict['tagtype'].fqin+":"+specdict['name']
    else:
        #specdict['fqin']=specdict['creator'].nick+"/"+specdict['name']
        specdict['fqin']=specdict['itemtype'].creator.nick+"/"+specdict['name']
    return specdict

def validatetypespec(specdict, spectype="itemtype"):
    keysneeded=MUSTHAVEKEYS[spectype]
    keyswehave=specdict.keys()
    for k in keysneeded:
        if k not in keyswehave:
            doabort('BAD_REQ', "Key %s not in spec for %s" % (k, spectype))
    specdict['fqin']=specdict['creator'].nick+"/"+specdict['name']
    return specdict

def _critsqlmaker(crit):
    rs=[]
    if len(crit.keys()) >0:
        for k in crit.keys():
            v=crit[k]
            print "type", type(v)
            if type(v)==types.StringType or type(v)==types.UnicodeType:
                v="'"+v+"'"
            rs.append("items."+k+'=='+v)
        return ','.join(rs)
    else:
        return None

def is_stringtype(v):
    if type(v)==types.StringType or type(v)==types.UnicodeType:
        return True
    else:
        return False

# 1. get's dont use currentuser so at a later point drop the currentuser there.
#   Since these are not exported we also might wanna underscore them
class Postdb(dbase.Database):

    def __init__(self, session):
        super(Postdb, self).__init__(session)
        self.whosdb=Whosdb(session)

   #######################################################################################################################
   #Internals. No protection on these

    def getItemType(self, currentuser, fullyQualifiedItemType):
        try:
            itemtype=self.session.query(ItemType).filter_by(fqin=fullyQualifiedItemType).one()
        except:
            doabort('NOT_FND', "ItemType %s not found" % fullyQualifiedItemType)
        return itemtype

    def getTagType(self, currentuser, fullyQualifiedTagType):
        try:
            tagtype=self.session.query(TagType).filter_by(fqin=fullyQualifiedTagType).one()
        except:
            doabort('NOT_FND', "TagType %s not found" % fullyQualifiedTagType)
        return tagtype

    def getPostingInGroup(self, currentuser, grp, item):
        try:
            itempost=self.session.query(ItemGroup).filter_by(group=grp, item=item).one()
        except:
            doabort('NOT_FND', "Posting in grp %s for item %s not found" % (grp.fqin, item.fqin))

    def getPostingInApp(self, currentuser, app, item):
        try:
            itempost=self.session.query(ItemApplication).filter_by(application=app, item=item).one()
        except:
            doabort('NOT_FND', "Posting in app %s for item %s not found" % (app.fqin, item.fqin))

    def getItem(self, currentuser, fullyQualifiedItemName):
        try:
            item=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        except:
            doabort('NOT_FND', "Item %s not found" % fullyQualifiedItemName)
        return item

    def getTag(self, currentuser, fullyQualifiedTagName):
        try:
            tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        except:
            doabort('NOT_FND', "Tag %s not found" % fullyQualifiedTagName)
        return tag

    def getTagging(self, currentuser, tag, item):
        try:
            itemtag=self.session.query(ItemTag).filter_by(tag=tag, item=item).one()
        except:
            doabort('NOT_FND', "Tagging for tag %s and item %s not found" % (tag.fqin, item.fqin))
        return itemtag

    def getTaggingsByItem(self, currentuser, item):
        try:
            itemtags=self.session.query(ItemTag).filter_by(item=item)
        except:
            doabort('NOT_FND', "Taggings for item %s not found" % item.fqin)
        return itemtags

    def getTaggingsByTag(self, currentuser, tag):
        try:
            itemtags=self.session.query(ItemTag).filter_by(tag=tag)
        except:
            doabort('NOT_FND', "Taggings for tag %s not found" % tag.fqin)
        return itemtags



    def getGroupTagging(self, currentuser, itemtag, grp):
        try:
            itemtaggrp=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        except:
            doabort('NOT_FND', "Tag %s for item %s for group %s not found" % (itemtag.tag.fqin, itemtag.item.fqin, grp.fqin))
        return itemtaggrp

    def getGroupTaggingsByTag(self, currentuser, tag, grp):
        try:
            itemtaggrps=self.session.query(TagitemGroup).filter_by(tag=tag, group=grp)
        except:
            doabort('NOT_FND', "Grptaggings for tag %s for group %s not found" % (tag.fqin,  grp.fqin))
        return itemtaggrps

    def getGroupTaggingsByItem(self, currentuser, item, grp):
        try:
            itemtaggrps=self.session.query(TagitemGroup).filter_by(item=item, group=grp)
        except:
            doabort('NOT_FND', "Grptaggings for item %s for group %s not found" % (item.fqin,  grp.fqin))
        return itemtaggrps

    def getAppTagging(self, currentuser, itemtag, app):
        try:
            itemtagapp=self.session.query(TagitemApplication).filter_by(itemtag=itemtag, application=app).one()
        except:
            doabort('NOT_FND', "Tag %s for item %s for application %s not found" % (itemtag.tag.fqin, itemtag.item.fqin, app.fqin))
        return itemtagapp

    def getAppTaggingsByTag(self, currentuser, tag, app):
        try:
            itemtagapps=self.session.query(TagitemApplication).filter_by(tag=tag, application=app)
        except:
            doabort('NOT_FND', "Apptaggings for tag %s for app %s not found" % (tag.fqin,  app.fqin))
        return itemtagapps

    def getAppTaggingsByItem(self, currentuser, item, app):
        try:
            itemtagapps=self.session.query(TagitemApplication).filter_by(item=item, application=app)
        except:
            doabort('NOT_FND', "Apptaggings for item %s for app %s not found" % (item.fqin,  app.fqin))
        return itemtagapps

    #######################################################################################################################

    def addItemType(self, currentuser, typespec):
        typespec=validatetypespec(typespec)
        try:
            itemtype=ItemType(**typespec)
        except:
            doabort('BAD_REQ', "Failed adding itemtype %s" % typespec['fqin'])
        self.session.add(itemtype)
        return OK

    def removeItemType(self, currentuser, fullyQualifiedItemType):
        itemtype=self.getItemType(currentuser, fullyQualifiedItemType)
        permit(currentuser==itemtype.creator or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        self.session.delete(itemtype)
        return OK

    def addTagType(self, currentuser, typespec):
        typespec=validatetypespec(typespec, spectype="tagtype")
        try:
            tagtype=TagType(**typespec)
        except:
            doabort('BAD_REQ', "Failed adding tagtype %s" % typespec['fqin'])
        self.session.add(tagtype)
        return OK

    def removeTagType(self, currentuser, fullyQualifiedTagType):
        tagtype=self.getTagType(currentuser, fullyQualifiedTagType)
        permit(currentuser==tagtype.creator or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        self.session.delete(tagtype)
        return OK

    #######################################################################################################################

    #Bug: prevent multiple postings by the same user, either at dbase or python level
    #THIRD PARTY MASQUERADABLE(TPM) eg current user=oauthed web service acting as user.
    #if item does not exist this will fail
    def postItemIntoGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName):
        ##Only for now as we wont allow third parties to save BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(itemorfullyQualifiedItemName):
            item=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            item=itemorfullyQualifiedItemName
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.whosdb.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName
        permit(self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s can post into it" % grp.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)

        try:
            newposting=ItemGroup(item=item, group=grp, user=useras, itemuri=item.uri, itemtype=item.itemtype)
        except:
            doabort('BAD_REQ', "Failed adding newposting of item %s into group %s." % (item.fqin, grp.fqin))
        self.session.add(newposting)
        fqgn=useras.nick+"/group:default"

        if grp.fqin!=fqgn:
            personalgrp=self.whosdb.getGroup(currentuser, fqgn)
            if item not in personalgrp.itemsposted:
                self.postItemIntoGroup(currentuser, useras, personalgrp, item)
        #self.commit()
        #print newitem.groupsin, "WEE", grp.itemsposted, newposting.itemtype.name
        #grp.groupitems.append(newitem)
        return OK

    def postItemPublic(self, currentuser, useras, itemorfullyQualifiedItemName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        self.postItemIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName)

    def removeItemFromGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName):
        if is_stringtype(itemorfullyQualifiedItemName):
            itemtoberemoved=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itemtoberemoved=itemorfullyQualifiedItemName
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.whosdb.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName
        postingtoremove=self.getPostingInGroup(currentuser, grp, itemtoberemoved)
        permit(useras==postingtoremove.user and self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s who posted this item can remove it from the group" % grp.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
        self.session.remove(postingtoremove)
        return OK

    def postItemIntoApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName):
        ##Only for now as we wont allow third parties to save BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(itemorfullyQualifiedItemName):
            item=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            item=itemorfullyQualifiedItemName
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.whosdb.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        permit(self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s can post into it" % app.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)

        try:
            newposting=ItemApplication(item=item, application=app, user=useras, itemuri=item.uri, itemtype=item.itemtype)
        except:
            doabort('BAD_REQ', "Failed adding newposting of item %s into app %s." % (item.fqin, app.fqin))
        self.session.add(newposting)
        fqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        if item not in personalgrp.itemsposted:
            self.postItemIntoGroup(currentuser, useras, personalgrp, item)
        #self.commit()
        #print newitem.groupsin, "WEE", grp.itemsposted
        #grp.groupitems.append(newitem)
        return OK

    def removeItemFromApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName):
        if is_stringtype(itemorfullyQualifiedItemName):
            itemtoberemoved=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itemtoberemoved=itemorfullyQualifiedItemName
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.whosdb.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        postingtoremove=self.getPostingInApp(currentuser, app, itemtoberemoved)
        permit(useras==postingtoremove.user and self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s who posted this item can remove it from the app" % app.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
        self.session.remove(postingtoremove)
        return OK

    #######################################################################################################################
    #Stuff for a single item
    #When a web service adds an item on their site, and we add it here as the web service user, do we save the item?
    #If we havent saved the item, can we post it to a group?: no Item id. Must we not make the web service save the
    #item first? YES. But there is no app. Aah this must be done outside in web service!!

    def saveItem(self, currentuser, useras, itemspec):
        ##Only for now as we wont allow third parties to save BUG
        #BUG2 now if another user has saed item we just get it! (like tag exists)
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        fqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        itemspec['itemtype']=self.getItemType(currentuser, itemspec['itemtype'])
        itemspec=validatespec(itemspec)

        #print itemspec
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            print "was the item found"
            newitem=self.getItemByFqin(currentuser, itemspec['fqin'])
        except:
            #the item was not found. Create it
            try:
                print "try creating item"
                newitem=Item(**itemspec)
            except:
                doabort('BAD_REQ', "Failed adding item %s" % itemspec['fqin'])
        self.session.add(newitem)
        return self.postItemIntoGroup(currentuser, useras, personalgrp, newitem)

    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        fqgn=useras.nick+"/group:default" #ALSO TRIGGER others (bug)
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        itemtoremove=self.getItem(currentuser, fullyQualifiedItemName)
        #should we do this. Or merely mark it removed.? TODO
        #protecting the masquerade needs to be done in web service
        permit(useras==itemtoremove.user, "Only user who saved this item can remove it")
        self.removeItemFromGroup(currentuser, useras, personalgrp, itemtoremove)

        #NEW: We did not nececerraily create this, so we cant remove!!! Even so implemen ref count as we can then do popularity
        #self.session.remove(itemtoremove)

    #######################################################################################################################
    # If tag exists we must use it instead of creating new tag
    # BUG: how to avoid multiple tags if name is same. We dont check description or anything?
    # we could insist that tagtype:tagname be unique, and description cant change that: i.e. the name argument must be unique
    # for an item. Lets do that for now. Or otherwise generate a random identifying hash or something.
    # how does this affect notes? How does a note have the identity a tag has? In this sense notes and comments
    # are fundamentally different to tags. note text, at some level should be in description. It would seem that names ought
    #to be used for subtypes of a tagtype. e.g. note:warning or tag:lensing. All too confusing. BUG
    #current thinking is that text of a note goes in the description, and there is a singleton note tag thats used again and again?
    #(singleton per user, that is) One thing to make it non-singleton would be to have the item as argument (not description)
    #or user could type the note (such as urgent, etc: perhaps even a tag)
    def tagItem(self, currentuser, useras, fullyQualifiedItemName, tagspec):
        tagspec['tagtype']=self.getTagType(currentuser, tagspec['tagtype'])
        tagspec=validatespec(tagspec, spectype='tag')
        ##Only for now as we wont allow third parties to tag BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        #BUG: the line below only allows tagging item that has been saved.
        #But it could have been saved by someone else. Consider this in your permits
        # Shouldnt a saved item need to be in a group or public for you to be able to do something with it
        #or should we handle this by UI and visibility
        #or should we take the position that a user must have saved an item hilself for it to be tagged
        #a DECISION needs to be made on this
        #THIS COULD BE FIXED WITH THE NEW ALBERTO NOTION OF ITEM YES
        itemtobetagged=self.getItem(currentuser, fullyQualifiedItemName)
        #BUG: this should make sure we are in user's default group: really?
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            print "was tha tag found"
            tag=self.getTag(currentuser, tagspec['fqin'])
        except:
            #the tag was not found. Create it
            try:
                print "try creating tag"
                newtag=Tag(**tagspec)
            except:
                doabort('BAD_REQ', "Failed adding tag %s" % tagspec['fqin'])
        self.session.add(newtag)
        print "newtagging"
        try:
            #Bug: one ought to search to see if tag exists and abort
            #Currently allow creating newtagging every time
            newtagging=ItemTag(item=itemtobetagged, tag=newtag, user=useras, 
                itemuri=itemtobetagged.uri, tagname=newtag.name, tagtype=tagspec['tagtype'], itemtype=itemtobetagged.itemtype)
        except:
            doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s" % (itemtobetagged.fqin, newtag.fqin))
        self.session.add(newtagging)
        fqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        #Add tag to default personal group
        print "adding to %s" % personalgrp.fqin
        self.postTaggingIntoGroupFromItemtag(currentuser, useras, personalgrp, newtagging)
        #print itemtobetagged.itemtags, "WEE", newtag.taggeditems, newtagging.tagtype.name
        return OK

    def untagItem(self, currentuser, useras, fullyQualifiedTagName, fullyQualifiedItemName):
        #Do not remove item, do not remove tag, do not remove tagging
        #just remove the tag from the personal group
        tag=self.getTag(currentuser, fullyQualifiedTagName)
        itemtobeuntagged=self.getItem(currentuser, fullyQualifiedItemName)
        #Does not remove the tag or the item. Just the tagging. WE WILL NOT REFCOUNT TAGS
        taggingtoremove=self.getTagging(currentuser, tag, itemtobeuntagged)
        permit(useras==taggingtoremove.user, "Only user who saved this item to the tagging %s can remove the tag from priv grp" % tag.fqin )
        #self.session.remove(taggingtoremove)
        fqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        #remove tag from user's personal group. Keep the tagging around
        self.removeTaggingFromGroup(currentuser, useras, personalgrp.fqin, itemtobeuntagged.fqin, tag.fqin)
        return OK


    #For the taggings being posted into groups, automatically put into personal group. Not needed, as when you get the itemtag which has the
    #item and tag, th tagItem function automatically did this for us
    def postTaggingIntoGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        ##Only for now as we wont allow third parties to save BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(itemorfullyQualifiedItemName):
            itm=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itm=itemorfullyQualifiedItemName
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.whosdb.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName

        #The itemtag must exist at first
        #NOT ALLOWING USER TO POST SOMEONE ELSES TAGGING INTO GROUP. (What about someone else's tag? We could use this for tag subtypig)
        #YES.
        #this is opposed to other items, once found anywhere, can be posted into group
        itemtag=self.getTagging(currentuser, tag, itm)
        permit(self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s can post into it" % grp.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into group %s" % grp.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
        print "ITEMTAG", itemtag, itm, grp, tag
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            newitg=TagitemGroup(itemtag=itemtag, group=grp, tagname=tag.name, tagtype=tag.tagtype, user=useras)
        except:
            doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in group %s" % (itm.fqin, tag.fqin, grp.fqin))

        self.session.add(newitg)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return OK

    def postTaggingPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        self.postTaggingIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName)

    def postTaggingIntoGroupFromItemtag(self, currentuser, useras, grouporfullyQualifiedGroupName, itemtag):
        ##Only for now as we wont allow third parties to save BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.whosdb.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        permit(self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s can post into it" % grp.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into group %s" % grp.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
        try:
            tag=itemtag.tag
            newitg=TagitemGroup(itemtag=itemtag, group=grp, tagname=tag.name, tagtype=tag.tagtype, user=useras)
        except:
            doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in group %s" % (itemtag.item.fqin, tag.fqin, grp.fqin))

        self.session.add(newitg)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return OK

    #BUG: currently not sure what the logic for everyone should be on this, or if it should even be supported
    #as other users have now seen stuff in the group. What happens to tagging. Leave alone for now.
    def removeTaggingFromGroup(self, currentuser, useras, fullyQualifiedGroupName, fullyQualifiedItemName, fullyQualifiedTagName):
        if is_stringtype(itemorfullyQualifiedItemName):
            itm=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itm=itemorfullyQualifiedItemName
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.whosdb.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        #The itemtag must exist at first
        itemtag=self.getTagging(currentuser, tag, itm)
        itgtoberemoved=self.getGroupTagging(currentuser, itemtag, grp)
        self.session.remove(itgtoberemoved)
        return OK

    def postItemAndTaggingIntoGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(itemorfullyQualifiedItemName):
            itm=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itm=itemorfullyQualifiedItemName
        if is_stringtype(grouporfullyQualifiedGroupName):
            grp=self.whosdb.getGroup(currentuser, grouporfullyQualifiedGroupName)
        else:
            grp=grouporfullyQualifiedGroupName
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        self.postItemIntoGroup(currentuser, useras, grp, itm)
        self.postTaggingIntoGroup(currentuser, useras, grp, itm, tag)

    def postItemAndTaggingPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        self.postItemAndTaggingIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName)


    #BUG: we are not requiring that item be posted into group or that tagging autopost it. FIXME
    def postTaggingIntoAppFromItemtag(self, currentuser, useras, apporfullyQualifiedAppName, itemtag):
        ##Only for now as we wont allow third parties to save BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.whosdb.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        #Note tagger need not be creator of item.

        permit(self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s can post into it" % app.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into app %s" % app.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)

        #The itemtag must exist at first
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            newita=TagitemApplication(itemtag=itemtag, application=app, tagname=tag.name, tagtype=tag.tagtype, user=useras)
        except:
            doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in app %s" % (itm.fqin, tag.fqin, app.fqin))    
        self.session.add(newita)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return OK

    def postTaggingIntoApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        ##Only for now as we wont allow third parties to save BUG
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(itemorfullyQualifiedItemName):
            itm=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itm=itemorfullyQualifiedItemName
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.whosdb.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        #Note tagger need not be creator of item.
        itemtag=self.getTagging(currentuser, tag, itm)

        permit(self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s can post into it" % app.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into app %s" % app.fqin)
        permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
            "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)

        #The itemtag must exist at first
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            newita=TagitemApplication(itemtag=itemtag, application=app, tagname=tag.name, tagtype=tag.tagtype, user=useras)
        except:
            doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in app %s" % (itm.fqin, tag.fqin, app.fqin))    
        self.session.add(newita)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return OK

    #BUG: currently not sure what the logic for everyone should be on this, or if it should even be supported
    #as other users have now seen stuff in the group. What happens to tagging. Leave alone for now.
    def removeTaggingFromApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        if is_stringtype(itemorfullyQualifiedItemName):
            itm=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itm=itemorfullyQualifiedItemName
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.whosdb.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        #The itemtag must exist at first
        itemtag=self.getTagging(currentuser, tag, itm)
        itatoberemoved=self.getAppTagging(currentuser, itemtag, app)
        self.session.remove(itatoberemoved)
        return OK

    def postItemAndTaggingIntoApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        if is_stringtype(itemorfullyQualifiedItemName):
            itm=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            itm=itemorfullyQualifiedItemName
        if is_stringtype(apporfullyQualifiedAppName):
            app=self.whosdb.getApp(currentuser, apporfullyQualifiedAppName)
        else:
            app=apporfullyQualifiedAppName
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        self.postItemIntoApp(currentuser, useras, app, itm)
        self.postTaggingIntoApp(currentuser, useras, app, itm, tag)
    #######################################################################################################################
    #BUG: currently not allowing tags to be removed due to cascading tagging removal issue thinking
    #eventually remove only that tagginh from all of an items tags


    #######################################################################################################################

    #ALL KINDS OF GETS
    #This gets the useras's stuff. Should there be permits instead. YES BUG! But we'll leave it for now
    #NEW: just gets item not saving of item in user's personal groups. This now means nick should no longer be used to get a users items.
    #BUG: this now seems similar to the get right at top of document. Perhaps this one should be the API facing one: protected.
    def getItemByFqin(self, currentuser, fullyQualifiedItemName):
        #fullyQualifiedItemName=nsuser.nick+"/"+itemname
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        try:
            itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        except:
            doabort('NOT_FND', "Item with name %s not saved by %s." % (fullyQualifiedItemName, useras.nick))
        return itm.info()

    #the uri can be saved my multiple users, which would give multiple results here. which user to use
    #should we not use useras. Ought we be getting from default group?
    #here I use useras, but suppose the useras is not the user himself or herself (ie currentuser !=useras)
    #then what? In other words if the currentuser is a group or app owner how should things be affected?
    #CURRENTLY DONT ALLOW THIS FUNC TO BE MASQUERADED.

    #so nor sure how useful as still comes from a users saving
    def getItemByURI(self, currentuser, useras, itemuri):
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        try:
            itm=self.session.query(Item).filter_by(uri=itemuri, creator=useras).one()
        except:
            doabort('NOT_FND', "Item with uri %s not saved by %s." % (itemuri, useras.nick))
        return itm.info()

    #######################################################################################################################
    #the ones in this section should go sway at some point. CURRENTLY Nminimal ERROR HANDLING HERE as selects should
    #return null arrays atleast

    def getItems(self, currentuser, useras, context=None, fqin=None, criteria={}):
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser,criteria['itemtype'])   
        if context == None:
            permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
            items=self.session.query(Item).filter_by(**criteria)
        elif context == 'group':
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            
            items=self.session.query(Item).select_from(join(Item, ItemGroup))\
                            .filter(ItemGroup.group==grp)\
                            .filter_by(**criteria)
        elif context == 'app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            items=self.session.query(Item).select_from(join(Item, ItemApplication))\
                            .filter(ItemApplication.application==app)\
                            .filter_by(**criteria)
        return [ele.info() for ele in items]

    #Not needed any more due to above but kept around for quicker use:
    # def getItemsForApp(self, currentuser, useras, fullyQualifiedAppName):
    #     app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
    #     return [ele.info() for ele in app.itemsposted]

    # def getItemsForGroup(self, currentuser, useras, fullyQualifiedGroupName):
    #     grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
    #     return [ele.info() for ele in grp.itemsposted]

    #we are doing joins here but ought we do subselects?
    def getItemsForUser(self, currentuser, useras, context=None, fqin=None, criteria={}):
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser,criteria['itemtype'])
        if context == None:
            permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
            fqin=useras.nick+"/group:default"
            grp=self.whosdb.getGroup(currentuser, fqin)
            items=self.session.query(Item).select_from(join(Item, ItemGroup))\
                                        .filter(ItemGroup.group==grp)\
                                        .filter_by(**criteria)
        elif context=='group':
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            items=self.session.query(Item).select_from(join(Item, ItemGroup))\
                                        .filter(ItemGroup.user==useras, ItemGroup.group==grp)\
                                        .filter_by(**criteria)
        elif context=='app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            items=self.session.query(Item).select_from(join(Item, ItemApplication))\
                                        .filter(ItemApplication.user==useras, ItemApplication.application==app)\
                                        .filter_by(**criteria)
        return [ele.info() for ele in items]

    #we're going through tagitem group and tagitemapp. Not sure this is the best choice.
    # def getTaggings(self, currentuser, useras, context=None, fqin=None, criteria={}):
    #     rhash={}
    #     titems={}
    #     if criteria.has_key('tagtype'):
    #         criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
    #     if context==None:
    #         taggings=self.session.query(ItemTag).filter_by(**criteria)
    #     elif context=='group':
    #         grp=self.session.query(Group).filter_by(fqin=fqin).one()
    #         #taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(user=useras, group=grp)]
    #         taggings=self.session.query(TagitemGroup)\
    #                                     .filter_by(group=grp)\
    #                                     .filter_by(**criteria)
    #         rhash['group']=grp.fqin
    #     elif context=='app':
    #         app=self.session.query(Application).filter_by(fqin=fqin).one()
    #         #taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(user=useras, application=app)]
    #         taggings=self.session.query(TagitemApplication)\
    #                                     .filter_by(application=app)\
    #                                     .filter_by(**criteria)
    #         rhash['app']=app.fqin
    #     for ele in taggings:
    #         eled=ele.info()
    #         eledfqin=eled['item']
    #         if not titems.has_key(eledfqin):
    #             titems[eledfqin]=[]
    #         titems[eledfqin].append(eled)
    #     rhash.update({'taggings':titems})
    #     return rhash

    # def getTaggingsForUser(self, currentuser, useras, context=None, fqin=None, criteria={}):
    #     rhash={}
    #     titems={}
    #     if criteria.has_key('tagtype'):
    #         criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
    #     if context==None:
    #         taggings=self.session.query(ItemTag).filter_by(user=useras).filter_by(**criteria)
    #     elif context=='group':
    #         grp=self.session.query(Group).filter_by(fqin=fqin).one()
    #         #taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(user=useras, group=grp)]
    #         taggings=self.session.query(TagitemGroup)\
    #                                     .filter_by(user=useras, group=grp)\
    #                                     .filter_by(**criteria)
    #         rhash['group']=grp.fqin
    #     elif context=='app':
    #         app=self.session.query(Application).filter_by(fqin=fqin).one()
    #         #taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(user=useras, application=app)]
    #         taggings=self.session.query(TagitemApplication)\
    #                                     .filter_by(user=useras, application=app)\
    #                                     .filter_by(**criteria)
    #         rhash['app']=app.fqin
    #     for ele in taggings:
    #         eled=ele.info()
    #         eledfqin=eled['item']
    #         if not titems.has_key(eledfqin):
    #             titems[eledfqin]=[]
    #         titems[eledfqin].append(eled)
    #     rhash.update({'user':useras.nick, 'taggings':titems})
    #     return rhash

    #Leave it be right now because we are running out of time

    #######################################################################################################################
    #Even this one could be done through the spec
    def getItemsForTag(self, currentuser, useras, tagorfullyQualifiedTagName, context=None, fqin=None, criteria={}):
        itemtype=None
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser, criteria['itemtype'])
            itemtype=criteria.pop('itemtype')
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        print "TAG", tag, tagorfullyQualifiedTagName
        #You would think that this ought to not be here because of the groups and apps, but remember, tags are specific
        #to users. Use the spec functions in this situation.
        permit(useras==tag.creator, "User must be creator of tag %s" % tag.fqin)
        if context is None:
            #Error buffeting here? BUG: is this allowed, even with lazy=dynamic 
            #BUG: will we leak? I dont think so, as tag is us, and hopefully we are only allowed to tag items we have personally saved :-)
            #Havent yet, and if we did that, then we dont need to look at personal group. Otherwise we do.
            items=tag.taggeditems.filter(_critsqlmaker(criteria))#BUG: this dosent work
            if itemtype:
                items=items.filter_by(itemtype=itemtype)
        elif context is 'group':
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            #bottom could be done as query on the assoc-proxy collection too! Is that more idiomatic? BUG (Could also be faster)
            #more likely somewhere else
            itemtaggrps=self.getGroupTaggingsByTag(tag=tag, group=grp).filter_by(**criteria)
            items=[ele.item for ele in itemtaggrps]
        elif context is 'app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            itemtagapps=self.getAppTaggingsByTag(tag=tag, application=app).filter_by(**criteria)
            items=[ele.item for ele in itemtagapps]
        return [ele.info() for ele in items]

    #what about user and perms here? who should be allowed? Perhs different for different ifs?
    #ie for regular only ads and user, for group, group owner and group users, ditto for app?
    #what about app and group?
    # def getItemsForTagname(self, currentuser, useras, tagname, context=None, fqin=None):
    #     tags=self.session.query(Tag).filter_by(name=tagname).all()
    #     if context is None:
    #         itemsnested = [tag.taggeditems for tag in tags]
    #     elif context=='group':
    #         grp=self.session.query(Group).filter_by(fqin=fqin).one()
    #         itemsnested=[]
    #         for tag in tags:
    #             itemsnested.append([ele.item for ele in self.session.query(TagitemGroup).filter_by(tag=tag, group=grp)])
    #     elif context=='app':
    #         app=self.session.query(Application).filter_by(fqin=fqin).one()
    #         itemsnested=[]
    #         for tag in tags:
    #             itemsnested.append([ele.item for ele in self.session.query(TagitemApplication).filter_by(tag=tag, application=app)])
        
    #     items = [inner for outer in itemsnested for inner in outer]
    #     return [ele.info() for ele in items]
   

 

    # def getItemsForTagtype(self, currentuser, useras, tagtypefqin, context=None, fqin=None):
    #     tagtypeobject=self.session.query(Tagtype).filter_by(fqin=tagtypefqin).one()
    #     tags=self.session.query(Tag).filter_by(tagtype=tagtypeobject).all()
    #     if context==None:
    #         itemsnested = [tag.taggeditems for tag in tags]
    #     elif context=='group':
    #         grp=self.session.query(Group).filter_by(fqin=fqin).one()
    #         itemsnested=[]
    #         for tag in tags:
    #             itemsnested.append([ele.item for ele in self.session.query(TagitemGroup).filter_by(tag=tag, group=grp)])
    #     elif context=='app':
    #         app=self.session.query(Application).filter_by(fqin=fqin).one()
    #         itemsnested=[]
    #         for tag in tags:
    #             itemsnested.append([ele.item for ele in self.session.query(TagitemApplication).filter_by(tag=tag, application=app)])
        
    #     items = [inner for outer in itemsnested for inner in outer]
    #     return [ele.info() for ele in items]



    #BUG: cant we use more direct collections in the simple cases?
    def getTagsForItem(self, currentuser, useras, itemorfullyQualifiedItemName, context=None, fqin=None, criteria={}):
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.getTagType(currentuser, criteria['tagtype'])
        if is_stringtype(itemorfullyQualifiedItemName):
            item=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            item=itemorfullyQualifiedItemName
        rhash={}
        titems={}
        if context==None:
            #we dont do this in general because as a group user I might want all tags in the group on an item i didnt create
            #BUG: model that in permits: for that answer: does item need to be owned by user, or posted into group by
            #user of group. So the itemgroup thing may be the thing to use BUGFIXED
            #BUG: so this is wrong now. Its not the item creator. But it must be in our personal group. Currently not permit-blocking
            #permit(useras==item.creator, "User must be creater of item %s" % item.fqin)
            taggings=self.getTaggingsByItem(currentuser, item).filter_by(**criteria)
        elif context=='group':
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            if item not in grp.itemsposted:
                doabort("BAD_REQ", "Item must be posted in this group for tags to be retrieved")
            taggings=self.getGroupTaggingsByItem(currentuser, item, grp).filter_by(**criteria)
            #taggings=self.session.query(TagitemGroup).filter(TagitemGroup.item_id==item.id, TagitemGroup.group==grp)
            rhash['group']=grp.fqin
        elif context=='app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            if item not in app.itemsposted:
                doabort("BAD_REQ", "Item must be posted in this app for tags to be retrieved")
            taggings=self.getAppTaggingsByItem(currentuser, item, app).filter_by(**criteria)
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash


    #BUG: the permitting here is not proper
    def _getTaggingsWithCriterion(self, currentuser, useras, context, fqin, criteria, rhash):
        itemtype=None
        userthere=False       
        itemselections={'itemname':'name', 'itemuri': 'uri', 'itemtype': 'itemtype'}
        tagselections={'tagname':'tagname', 'tagtype': 'tagtype'}
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.getTagType(currentuser, criteria['tagtype'])
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser, criteria['itemtype'])
            itemtype=criteria.pop('itemtype')
        if criteria.has_key('userthere'):
            userthere=criteria.pop('userthere')

        itemcriteria={}
        tagcriteria={}
        for key in criteria.keys():
            if key in itemselections.keys():
                itemcriteria[itemselections[key]]=criteria[key]
            elif key in tagselections.keys():
                tagcriteria[tagselections[key]]=criteria[key]
        itemsql=_critsqlmaker(itemcriteria)
        #No error handling as we should atleast get empty sets
        if context==None:
            taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter_by(**tagcriteria)
            if userthere:
                permit(currentuser==useras, "Current user is not useras")
                taggings=taggings.filter(ItemTag.user==useras)
            else:
                permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
        elif context=='group':            
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            taggingothers=self.session.query(TagitemGroup).filter_by(group=grp).filter_by(**tagcriteria)
            rhash['group']=grp.fqin
            taggings=taggingothers.join(Item, TagitemGroup.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemGroup.user==useras)
        elif context=='app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            taggingothers=self.session.query(TagitemApplication).filter_by(application=app).filter_by(**tagcriteria)
            rhash['app']=app.fqin
            taggings=taggingothers.join(Item, TagitemApplication.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemApplication.user==useras)
        if userthere:
            rhash['user']=useras.nick
        if itemtype:
            taggings=taggings.filter(Item.itemtype==itemtype)
        if itemsql:
            taggings=taggings.filter(itemsql)

        return taggings

    def getTaggingForItemspec(self, currentuser, useras, context=None, fqin=None, criteria={}):
        rhash={}
        titems={}
        taggings=self._getTaggingsWithCriterion(currentuser, useras, context, fqin, criteria, rhash)
        for ele in taggings:
            eled=ele.info()
            #print "eled", eled
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'taggings':titems})
        return rhash

    def getItemsForTagspec(self, currentuser, useras, context=None, fqin=None, criteria={}):
        rhash={}
        titems={}
        taggings=self._getTaggingsWithCriterion(currentuser, useras, context, fqin, criteria, rhash)

        #Perhaps fluff this up with tags in a reasonable way! TODO
        for ele in taggings:
            eled=ele.info()
            #print "eled", eled
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=eled['iteminfo']
        rhash.update({'items':titems.values()})
        return rhash

    # def getTagsForItemuri(self, currentuser, useras, itemuri, context=None, fqin=None):
    #     rhash={}
    #     titems={}
    #     if context is None:
    #         taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter(Item.uri==itemuri).all()
    #     elif context is 'group':
    #         grp=self.session.query(Group).filter_by(fqin=fqin).one()
    #         taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).select_from(join(TagitemGroup, Item)).filter(Item.uri==itemuri,TagitemGroup.group==grp)]
    #         rhash['group']=grp.fqin
    #     elif context is 'app':
    #         app=self.session.query(Application).filter_by(fqin=fqin).one()
    #         taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).select_from(join(TagitemApplication, Item)).filter(Item.uri==itemuri,TagitemApplication.application==app)]
    #         rhash['app']=app.fqin
    #     for ele in taggings:
    #         eled=ele.info()
    #         if not titems.has_key(ele.item.fqin):
    #             titems[ele.item.fqin]=[]
    #         titems[ele.item.fqin].append(eled)
    #     rhash.update({'user':useras.nick, 'taggings':titems})
    #     return rhash

    # def getTagsForItemtype(self, currentuser, useras, itemtypefqin, context=None, fqin=None):
    #     itemtypeobject=self.session.query(Itemtype).filter_by(fqin=itemtypefqin).one()
    #     rhash={}
    #     titems={}
    #     if context is None:
    #         taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter(Item.itemtype==itemtypeobject).all()
    #     elif context is 'group':
    #         grp=self.session.query(Group).filter_by(fqin=fqin).one()
    #         taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).select_from(join(TagitemGroup, Item)).filter(Item.itemtype==itemtypeobject,TagitemGroup.group==grp)]
    #         rhash['group']=grp.fqin
    #     elif context is 'app':
    #         app=self.session.query(Application).filter_by(fqin=fqin).one()
    #         taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).select_from(join(TagitemApplication, Item)).filter(Item.itemtype==itemtypeobject,TagitemApplication.application==app)]
    #         rhash['app']=app.fqin
    #     for ele in taggings:
    #         eled=ele.info()
    #         if not titems.has_key(ele.item.fqin):
    #             titems[ele.item.fqin]=[]
    #         titems[ele.item.fqin].append(eled)
    #     rhash.update({'user':useras.nick, 'taggings':titems})
    #     return rhash


def initialize_application(sess):
    currentuser=None
    whosdb=Whosdb(sess)
    postdb=Postdb(sess)
    adsuser=whosdb.getUserForNick(currentuser, "ads")
    currentuser=adsuser
    postdb.addItemType(currentuser, dict(name="pub", creator=adsuser))
    postdb.addItemType(currentuser, dict(name="pub2", creator=adsuser))
    postdb.addTagType(currentuser, dict(name="tag", creator=adsuser))
    postdb.addTagType(currentuser, dict(name="tag2", creator=adsuser))
    rahuldave=whosdb.getUserForNick(currentuser, "rahuldave")
    postdb.commit()
    currentuser=rahuldave
    postdb.saveItem(currentuser, rahuldave, dict(name="hello kitty", 
            uri='xxxlm', itemtype="ads/pub", creator=rahuldave))
    postdb.saveItem(currentuser, rahuldave, dict(name="hello doggy", 
            uri='xxxlm-d', itemtype="ads/pub2", creator=rahuldave))
    postdb.commit()
    print "here"
    postdb.tagItem(currentuser, rahuldave, "ads/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="stupid"))
    print "W++++++++++++++++++"
    postdb.tagItem(currentuser, rahuldave, "ads/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="dumb"))
    postdb.tagItem(currentuser, rahuldave, "ads/hello doggy", dict(tagtype="ads/tag", creator=rahuldave, name="dumbdog"))
    postdb.tagItem(currentuser, rahuldave, "ads/hello doggy", dict(tagtype="ads/tag2", creator=rahuldave, name="dumbdog2"))
    postdb.commit()
    print "LALALALALA"
    #Wen a tagging is posted to a group, the item should be autoposted into there too BUG NOT ONE NOW
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "ads/hello kitty")
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "ads/hello doggy")
    postdb.postItemIntoApp(currentuser,rahuldave, "ads/app:publications", "ads/hello doggy")
    print "PTGS"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello kitty", "rahuldave/ads/tag:stupid")
    print "1"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello kitty", "rahuldave/ads/tag:dumb")
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello doggy", "rahuldave/ads/tag:dumbdog")
    print "2"
    postdb.postTaggingIntoApp(currentuser, rahuldave, "ads/app:publications", "ads/hello doggy", "rahuldave/ads/tag:dumbdog")
    print "HOOCH"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello doggy", "rahuldave/ads/tag2:dumbdog2")
    postdb.postTaggingIntoApp(currentuser, rahuldave, "ads/app:publications", "ads/hello doggy", "rahuldave/ads/tag2:dumbdog2")

    postdb.commit()

class TestB(tbase.TBase):

    def test_something(self):
        print "HELLO"
        sess=self.session
        initialize_application(sess)
        currentuser=None
        whosdb=Whosdb(sess)
        postdb=Postdb(sess)
        adsuser=whosdb.getUserForNick(currentuser, "ads")
        currentuser=adsuser
        postdb.addItemType(currentuser, dict(name="pub", creator=adsuser))
        postdb.addTagType(currentuser, dict(name="tag", creator=adsuser))
        rahuldave=whosdb.getUserForNick(currentuser, "rahuldave")
        postdb.commit()
        currentuser=rahuldave
        itspec={}
        postdb.saveItem(currentuser, rahuldave, dict(name="hello kitty", 
                uri='xxxlm', itemtype="ads/pub", creator=rahuldave, fqin="rahuldave/hello kitty"))
        whosdb.commit()
        postdb.commit()
        postdb.tagItem(currentuser, rahuldave, "rahuldave/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="stupid paper"))
        postdb.commit()
        #Wen a tagging is posted to a group, the item should be autoposted into there too BUG NOT ONE NOW
        postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty")
        postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty", "rahuldave/stupid paper")
        postdb.commit()
        print postdb.getTaggingForUser(currentuser, rahuldave)
        print postdb.getTaggingForUser(currentuser, rahuldave, "group", "rahuldave/group:ml")
        print postdb.getTaggingForGroup(currentuser, rahuldave, "rahuldave/group:ml")
        print postdb.getItemsForGroup(currentuser, rahuldave, "rahuldave/group:ml")
        #BUG everything MUST be autoposted to private user group
        print postdb.getItemsForUser(currentuser, rahuldave)
        print postdb.getItemsForUser(currentuser, rahuldave, "group", "rahuldave/group:ml")
        #print postdb.getItemsForTag(currentuser, rahuldave, "rahuldave/stupid paper", "group", "rahuldave/group:ml")
        #whosdb.edu()

if __name__=="__main__":
    import os, os.path
    # if os.path.exists(config.DBASE_FILE):
    #     os.remove(config.DBASE_FILE)
    engine, db_session = dbase.setup_db(config.DBASE_FILE)
    dbase.init_db(engine)
    initialize_application(db_session)