from classes import *
from whos import Whosdb, initialize_application
import tbase
import dbase
import types
import config
from sqlalchemy.orm import join, aliased
from permissions import permit
from errors import abort, doabort
from sqlalchemy import desc
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

ORDERDICT={
    'uri':Item.uri,
    'name':Item.name,
    'whencreated':Item.whencreated,
    'tagname':ItemTag.tagname,
    'tagtype':ItemTag.tagtype,
    'whentagged':ItemTag.whentagged,
    'itemuri':Item.uri,
    'itemname':Item.name,
    'itemwhencreated':Item.whencreated,
    'itemtype':Item.itemtype,
    'groupwhenposted':ItemGroup.whenposted,
    'appwhenposted': ItemApplication.whenposted,
    'groupwhentagposted': TagitemGroup.whentagposted,
    'appwhentagposted': TagitemApplication.whentagposted
}

def FILTERDICT(tagctxt):
    thedict={
        'uri':Item.uri,
        'name':Item.name,
        'whencreated':Item.whencreated,
        'tagname':tagctxt.tagname,
        'tagtype':tagctxt.tagtype,
        'whentagged':ItemTag.whentagged,
        'itemuri':Item.uri,
        'itemname':Item.name,
        'itemwhencreated':Item.whencreated,
        'itemtype':Item.itemtype,
        'groupwhenposted':ItemGroup.whenposted,
        'appwhenposted': ItemApplication.whenposted,
        'groupwhentagposted': TagitemGroup.whentagposted,
        'appwhentagposted': TagitemApplication.whentagposted
    }
    return thedict
#as a result of not having whenposteds in itemtaggroup type things, we cant sort taggings based on when the item was posted into the
#group, which is arguably quite useful BUG: we should have this: but first we must answer: does the item need to be in the group?

def _getOrder(fieldvallist, orderer, extender=[]):
    fieldvallist.extend(extender)
    print fieldvallist, orderer
    if len(orderer)>0:
        outorderer=[]
        for ele in orderer:
            print "ELE", ele
            orderersplit=ele.split(':')
            if len(orderersplit)==2:
                order_by, updown=orderersplit
                if updown not in ['asc', 'desc']:
                    updown='asc'
            elif len(orderersplit)==1:
                order_by=orderersplit[0]
                updown='asc'
            else:
                return []
            if order_by in fieldvallist:
                print 'ob', order_by
                if updown=='asc':
                    oo = ORDERDICT[order_by]
                elif updown=='desc':
                    oo = desc(ORDERDICT[order_by])
                outorderer.append(oo)
        print "oooo", outorderer
        return outorderer
    return []

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
            # import sys
            # print sys.exc_info()
            doabort('BAD_REQ', "Failed adding itemtype %s" % typespec['fqin'])
        self.session.add(itemtype)
        return itemtype

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
        return tagtype

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
            print "ITEMGROUP", grp.fqin, item.name
            newposting=ItemGroup(item=item, group=grp, user=useras, itemuri=item.uri, itemtype=item.itemtype)
        except:
            doabort('BAD_REQ', "Failed adding newposting of item %s into group %s." % (item.fqin, grp.fqin))
        self.session.add(newposting)
        fqgn=useras.nick+"/group:default"

        if grp.fqin!=fqgn:
            personalgrp=self.whosdb.getGroup(currentuser, fqgn)
            if item not in personalgrp.itemsposted:
                print "NOT IN PERSONAL GRP"
                self.postItemIntoGroup(currentuser, useras, personalgrp, item)
        #self.commit() is this needed?
        #print newitem.groupsin, "WEE", grp.itemsposted, newposting.itemtype.name
        #grp.groupitems.append(newitem)
        return item

    def postItemPublic(self, currentuser, useras, itemorfullyQualifiedItemName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        itm=self.postItemIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName)
        return itm

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
            print "ITEMAPP", app.fqin, item.name
            newposting=ItemApplication(item=item, application=app, user=useras, itemuri=item.uri, itemtype=item.itemtype)
        except:
            doabort('BAD_REQ', "Failed adding newposting of item %s into app %s." % (item.fqin, app.fqin))
        self.session.add(newposting)
        #COMMENTING OUT as cant think of situation where a post into app ought to trigger personal group saving
        # fqgn=useras.nick+"/group:default"
        # personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        # if item not in personalgrp.itemsposted:
        #     self.postItemIntoGroup(currentuser, useras, personalgrp, item)
        #self.commit() #Needed as otherwise .itemsposted fails:
        #print newitem.groupsin, "WEE", grp.itemsposted
        #grp.groupitems.append(newitem)
        print "FINIAH APP POST"
        return item

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
        print "ghhh", itemspec
        permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        fqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        itemspec['itemtype']=self.getItemType(currentuser, itemspec['itemtype'])
        itemspec=validatespec(itemspec)

        print 'ggg', itemspec
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            print "was the item found?"
            newitem=self.getItemByFqin(currentuser, itemspec['fqin'])
        except:
            #the item was not found. Create it
            try:
                print "try creating item"
                print "ITSPEC", itemspec
                print '//////////////////////////'
                newitem=Item(**itemspec)
                print '?????//////////////////////////'
                # print "Newitem is", newitem.info()
            except:
                # import sys
                # print sys.exc_info()
                doabort('BAD_REQ', "Failed adding item %s" % itemspec['fqin'])
        self.session.add(newitem)
        appstring=newitem.itemtype.app

        print "APPSTRING\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\", appstring
        itemtypesapp=self.whosdb.getApp(currentuser, appstring)
        self.postItemIntoGroup(currentuser, useras, personalgrp, newitem)
        print '**********************'        
        #IN LIEU OF ROUTING
        self.postItemIntoApp(currentuser, useras, itemtypesapp, newitem)
        print '&&&&&&&&&&&&&&&&&&&&&&', 'FINISHED SAVING'
        return newitem

    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        fqgn=useras.nick+"/group:default" #ALSO TRIGGER others (bug)
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        itemtoremove=self.getItem(currentuser, fullyQualifiedItemName)
        #should we do this. Or merely mark it removed.? TODO
        #protecting the masquerade needs to be done in web service
        permit(useras==itemtoremove.user, "Only user who saved this item can remove it")
        self.removeItemFromGroup(currentuser, useras, personalgrp, itemtoremove)
        return OK
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
        return newtag, newtagging

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
        return itemtag, newitg

    def postTaggingPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        return self.postTaggingIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName)

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
        return newitg

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
        item=self.postItemIntoGroup(currentuser, useras, grp, itm)
        itemtag, itg = self.postTaggingIntoGroup(currentuser, useras, grp, itm, tag)
        return itemtag, itg

    def postItemAndTaggingPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        return self.postItemAndTaggingIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName)


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
        return newita

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
        return itemtag, newita

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
        item=self.postItemIntoApp(currentuser, useras, app, itm)
        itemtag, ita=self.postTaggingIntoApp(currentuser, useras, app, itm, tag)
        return itemtag, ita
    #######################################################################################################################
    #BUG: currently not allowing tags to be removed due to cascading tagging removal issue thinking
    #eventually remove only that tagginh from all of an items tags


    #######################################################################################################################

    #ALL KINDS OF GETS
    #This gets the useras's stuff. Should there be permits instead. YES BUG! But we'll leave it for now
    #NEW: just gets item not saving of item in user's personal groups. This now means nick should no longer be used to get a users items.
    #BUG: this now seems similar to the get right at top of document. Perhaps this one should be the API facing one: protected.
    #NOTE: dosent matter what the currentuser is in this case
    #also bug: no filtering information by user. check web service
    def getItemByFqin(self, currentuser, fullyQualifiedItemName):
        #fullyQualifiedItemName=nsuser.nick+"/"+itemname
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        try:
            itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        except:
            doabort('NOT_FND', "Item with name %s not found." % fullyQualifiedItemName)
        return itm.info()

    #the uri can be saved my multiple users, which would give multiple results here. which user to use
    #should we not use useras. Ought we be getting from default group?
    #here I use useras, but suppose the useras is not the user himself or herself (ie currentuser !=useras)
    #then what? In other words if the currentuser is a group or app owner how should things be affected?
    #CURRENTLY DONT ALLOW THIS FUNC TO BE MASQUERADED.

    #so nor sure how useful as still comes from a users saving
    #BUG ditto here as above on the filtering of info()
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

 

    #Not needed any more due to above but kept around for quicker use:
    # def getItemsForApp(self, currentuser, useras, fullyQualifiedAppName):
    #     app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
    #     return [ele.info() for ele in app.itemsposted]

    # def getItemsForGroup(self, currentuser, useras, fullyQualifiedGroupName):
    #     grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
    #     return [ele.info() for ele in grp.itemsposted]
    #No group by's so multiple objects for same item depending on the postings
    def _doItemFilter(self, context, userwanted, contextobject, contextitemobject, criteria={}, fvlist={}, orderer={}, additional=[]):
        if context=='group':
            ciocoll=ItemGroup.group
        elif context=='app':
            ciocoll=ItemApplication.application
        else:
            ciocoll=None
        if context==None:
            tuples=self.session.query(Item, 'NULL')
        else:
            tuples=self.session.query(Item, contextitemobject.whenposted)
        if userwanted==None:
            if context==None:
                tuples=tuples.filter_by(**criteria)
            else:
                tuples=tuples.select_from(join(Item, contextitemobject))\
                                            .filter(ciocoll==contextobject)\
                                            .filter_by(**criteria)
        else:
            tuples=tuples.select_from(join(Item, contextitemobject))\
                                            .filter(contextitemobject.user==userwanted, ciocoll==contextobject)\
                                            .filter_by(**criteria)
        order_by=_getOrder(fvlist, orderer, additional)
        if len(order_by)>0:
            tuples=tuples.order_by(*order_by)
        items=[t[0] for t in tuples]
        whenposteds=[t[1] for t in tuples]
        return items, whenposteds

    def getItems(self, currentuser, useras, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        userthere=False
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser,criteria['itemtype'])
        if criteria.has_key('userthere'):
            userthere=criteria.pop('userthere')
        if context == None:
            if userthere:
                permit(currentuser==useras, "Current user is not useras")
                fqin=useras.nick+"/group:default"
                grp=self.whosdb.getGroup(currentuser, fqin)
                items,whenposteds=self._doItemFilter(context, useras, grp, ItemGroup, criteria, fvlist, orderer)
            else:
                permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
                items, whenposteds = self._doItemFilter(context, None, None, None, criteria, fvlist, orderer)
            #permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
            #items, whenposteds = self._doItemFilter(context, None, None, None, criteria, fvlist, orderer)
        elif context == 'group':
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp) or self.whosdb.isSystemUser(currentuser),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            additional=['groupwhenposted']
            if userthere:
                items,whenposteds=self._doItemFilter(context, useras, grp, ItemGroup, criteria, fvlist, orderer, additional)
            else:
                items, whenposteds = self._doItemFilter(context, None, grp, ItemGroup, criteria, fvlist, orderer, additional)
        elif context == 'app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app) or self.whosdb.isSystemUser(currentuser),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            additional=['appwhenposted']
            if userthere:
                items,whenposteds=self._doItemFilter(context, useras, app, ItemApplication, criteria, fvlist, orderer, additional)
            else:
                items,whenposteds=self._doItemFilter(context, None, app, ItemApplication, criteria, fvlist, orderer, additional)

        eleinfo=[ele.info(useras) for ele in items]
        for i in range(len(eleinfo)):
            if whenposteds[i]==None:
                eleinfo[i]['whenposted']=None
            else:
                eleinfo[i]['whenposted']=whenposteds[i].isoformat()

        return eleinfo



    
    #BUG: check for permitting bugs
    def _getTaggingsWithCriterion(self, currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer):
        userthere=False       
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.getTagType(currentuser, criteria['tagtype'])
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser, criteria['itemtype'])
        if criteria.has_key('userthere'):
            userthere=criteria.pop('userthere')
        filterlist=[]

        if context==None:
            thechoice=ItemTag
            taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item))
            if userthere:
                permit(currentuser==useras, "Current user is not useras")
                taggings=taggings.filter(ItemTag.user==useras)
            else:
                permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
            additional=[]
        elif context=='group':
            thechoice=TagitemGroup         
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp) or self.whosdb.isSystemUser(currentuser),
                "Only member of group %s allowed" % grp.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            taggingothers=self.session.query(TagitemGroup).filter_by(group=grp)
            taggings=taggingothers.join(Item, TagitemGroup.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemGroup.user==useras)
            additional=['groupwhentagposted']
        elif context=='app':
            thechoice=TagitemApplication
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app) or self.whosdb.isSystemUser(currentuser),
                "Only member of app %s allowed" % app.fqin)
            permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
                "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            taggingothers=self.session.query(TagitemApplication).filter_by(application=app)
            rhash['app']=app.fqin
            taggings=taggingothers.join(Item, TagitemApplication.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemApplication.user==useras)
            additional=['appwhentagposted']
        #this does not prevent something from apps being used in something from groups, but i think only the ordering is
        #not common so its ok.
        for ele in criteria.keys():
            taggings=taggings.filter(FILTERDICT(thechoice)[ele] == criteria[ele])
        if userthere:
            rhash['user']=useras.nick
        order_by=_getOrder(fvlist, orderer, additional)
        if len(order_by)>0:
            taggings=taggings.order_by(*order_by)
        return taggings

    def getTaggingForItemspec(self, currentuser, useras, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        rhash={}
        titems={}
        taggings=self._getTaggingsWithCriterion(currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer)
        for ele in taggings:
            eled=ele.info(useras)
            #print "eled", eled
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'taggings':titems})
        return rhash

    def getItemsForTagspec(self, currentuser, useras, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        rhash={}
        titems={}
        taggings=self._getTaggingsWithCriterion(currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer)

        #Perhaps fluff this up with tags in a reasonable way! TODO BUG: want as only the items show and not the tag,
        #or immediate counts, or something like that
        for ele in taggings:
            eled=ele.info(useras)
            print "eled", eled['taginfo']
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=eled['iteminfo']
        rhash.update({'items':titems.values()})
        return rhash


    def getItemsForTag(self, currentuser, useras, tagorfullyQualifiedTagName, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        #in addition to whatever criteria (which ones are allowed ought to be in web service or here?) are speced
        #we need to get the tag
        rhash={}
        if is_stringtype(tagorfullyQualifiedTagName):
            tag=self.getTag(currentuser, tagorfullyQualifiedTagName)
        else:
            tag=tagorfullyQualifiedTagName
        print "TAG", tag, tagorfullyQualifiedTagName
        #You would think that this ought to not be here because of the groups and apps, but remember, tags are specific
        #to users. Use the spec functions in this situation.
        permit(useras==tag.creator, "User must be creator of tag %s" % tag.fqin)
        criteria['tagtype']=tag.tagtype.fqin
        criteria['tagname']=tag.name
        rhash=self.getItemsForTagspec(currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer)
        return rhash


    #BUG: cant we use more direct collections in the simple cases?
    def getTagsForItem(self, currentuser, useras, itemorfullyQualifiedItemName, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        rhash={}
        titems={}
        if is_stringtype(itemorfullyQualifiedItemName):
            item=self.getItem(currentuser, itemorfullyQualifiedItemName)
        else:
            item=itemorfullyQualifiedItemName

        #BUG: whats the security I can see the item?
        criteria['name']=item.name
        criteria['itemtype']=item.itemtype.fqin
        rhash=self.getTaggingForItemspec(currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer)
        return rhash


def initialize_application(sess):
    currentuser=None
    whosdb=Whosdb(sess)
    postdb=Postdb(sess)
    adsuser=whosdb.getUserForNick(currentuser, "ads")
    #adsapp=whosdb.getApp(adsuser, "ads/app:publications")
    currentuser=adsuser
    postdb.addItemType(currentuser, dict(name="pub", creator=adsuser, app="ads/app:publications"))
    postdb.addItemType(currentuser, dict(name="pub2", creator=adsuser, app="ads/app:publications"))
    postdb.addTagType(currentuser, dict(name="tag", creator=adsuser, app="ads/app:publications"))
    postdb.addTagType(currentuser, dict(name="tag2", creator=adsuser, app="ads/app:publications"))
    postdb.addTagType(currentuser, dict(name="note", creator=adsuser, app="ads/app:publications"))
    postdb.commit()


def initialize_testing(db_session):
    whosdb=Whosdb(db_session)
    postdb=Postdb(db_session)

    currentuser=None
    adsuser=whosdb.getUserForNick(currentuser, "ads")
    currentuser=adsuser

    rahuldave=whosdb.getUserForNick(currentuser, "rahuldave")
    postdb.commit()
    currentuser=rahuldave
    #run this as rahuldave? Whats he point of useras then?
    postdb.saveItem(currentuser, rahuldave, dict(name="hello kitty", 
            uri='xxxlm', itemtype="ads/pub", creator=rahuldave))
    #postdb.commit()
    postdb.saveItem(currentuser, rahuldave, dict(name="hello doggy", 
            uri='xxxlm-d', itemtype="ads/pub2", creator=rahuldave))
    postdb.commit()
    print "here"
    postdb.tagItem(currentuser, rahuldave, "ads/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="stupid"))
    print "W++++++++++++++++++"
    postdb.tagItem(currentuser, rahuldave, "ads/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="dumb"))
    postdb.tagItem(currentuser, rahuldave, "ads/hello kitty", dict(tagtype="ads/note", 
        creator=rahuldave, name="somethingunique1", description="this is a note for the kitty"))

    postdb.tagItem(currentuser, rahuldave, "ads/hello doggy", dict(tagtype="ads/tag", creator=rahuldave, name="dumbdog"))
    postdb.tagItem(currentuser, rahuldave, "ads/hello doggy", dict(tagtype="ads/tag2", creator=rahuldave, name="dumbdog2"))
    postdb.tagItem(currentuser, rahuldave, "ads/hello kitty", dict(tagtype="ads/note", 
        creator=rahuldave, name="somethingunique2", description="this is a note for the doggy"))

    postdb.commit()
    print "LALALALALA"
    #Wen a tagging is posted to a group, the item should be autoposted into there too BUG NOT ONE NOW
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "ads/hello kitty")
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "ads/hello doggy")
    #NOT NEEDED GOT FROM DEFAULT: BUG SHOULD ERROR OUT GRACEFULLY OR BE IDEMPOTENT
    #postdb.postItemIntoApp(currentuser,rahuldave, "ads/app:publications", "ads/hello doggy")
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
    datadict={'itemtype': 'ads/pub', 
                'uri': u'1884AnHar..14....1.', 
                'name': u'Description of photometer.'}    #postdb.saveItem(currentuser, rahuldave, datadict)


if __name__=="__main__":
    import os, os.path
    # if os.path.exists(config.DBASE_FILE):
    #     os.remove(config.DBASE_FILE)
    engine, db_session = dbase.setup_db(config.DBASE_FILE)
    dbase.init_db(engine)
    initialize_application(db_session)
    initialize_testing(db_session)