from classes import *
from whos import Whosdb, initialize_application
import tbase
import dbase
import types
import config
from sqlalchemy.orm import join, aliased
from permissions import permit, authorize
from permissions import authorize_context_owner, authorize_context_member
from errors import abort, doabort
from sqlalchemy import desc
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
OK=200

#pubsub to be used in conjunction with the access table to get stuff into all groups.
#remember to have a proper exception mechanism

##Issues
# 1. its not clear how, or that we are enforcing uniqieness at many place, for.eg, nick/uri or nick/name
# 2. Add last updated to tag's and let apps and groups get this
# 3. Instead of doAbort using flask exceptions, it should use ours and we should just map to handle by http layer
# 4. shouldnt all lookups on currentuser really be on useras? fix this when doing permits

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

#TODO: we now have whentagposted in classes.py ItemTagGroup and such. Spec out how to sort on it.
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
    if not specdict.has_key('uri'):
        specdict['uri']=specdict['name']
    if spectype=="tag":
        specdict['fqin']=specdict['creator'].nick+"/"+specdict['tagtype'].fqin+":"+specdict['uri']
        specdict['itemtype_id']=specdict['tagtype'].itemtype_id
    else:
        #specdict['fqin']=specdict['creator'].nick+"/"+specdict['name']
        specdict['fqin']=specdict['itemtype'].creator.nick+"/"+specdict['uri']
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


def _item(currentuser, db,  itemorfullyQualifiedItemName):
    if is_stringtype(itemorfullyQualifiedItemName):
        item=db.getItem(currentuser, itemorfullyQualifiedItemName)
    else:
        item=itemorfullyQualifiedItemName
    return item

def _group(currentuser, db,  grouporfullyQualifiedGroupName):
    if is_stringtype(grouporfullyQualifiedGroupName):
        grp=db.getGroup(currentuser, grouporfullyQualifiedGroupName)
    else:
        grp=grouporfullyQualifiedGroupName
    return grp

def _app(currentuser, db, apporfullyQualifiedAppName):
    if is_stringtype(apporfullyQualifiedAppName):
        app=db.getApp(currentuser, apporfullyQualifiedAppName)
    else:
        app=apporfullyQualifiedAppName
    return app

def _tag(currentuser, db,  tagorfullyQualifiedTagName):
    if is_stringtype(tagorfullyQualifiedTagName):
        tag=db.getTag(currentuser, tagorfullyQualifiedTagName)
    else:
        tag=tagorfullyQualifiedTagName
    return tag

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

    def getPostingInGroup(self, currentuser, useras, grp, item):
        try:
            itempost=self.session.query(ItemGroup).filter_by(group=grp, item=item, user=useras).one()
        except:
            doabort('NOT_FND', "Posting in grp %s for item %s not found" % (grp.fqin, item.fqin))
        return itempost

    def getPostingInApp(self, currentuser, useras, app, item):
        try:
            itempost=self.session.query(ItemApplication).filter_by(application=app, item=item, user=useras).one()
        except:
            doabort('NOT_FND', "Posting in app %s for item %s not found" % (app.fqin, item.fqin))
        return itempost

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

    #BUG: the three andusers funcs below, should they be permitted wrt currentuser? and if not how do we distinguish
    #general usability functions from external facing post.py funcs? come up with a convention
    def getTaggingsByItemAndUser(self, currentuser, useras, item):
        try:
            itemtags=self.session.query(ItemTag).filter_by(item=item, user=useras)
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


    def getGroupTaggingsByItemAndUser(self, currentuser, useras, item, grp):
        try:
            itemtaggrps=self.session.query(TagitemGroup).filter_by(item=item, group=grp, user=useras)
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

    def getAppTaggingsByItemAndUser(self, currentuser, useras, item, app):
        try:
            itemtagapps=self.session.query(TagitemApplication).filter_by(item=item, application=app, user=useras)
        except:
            doabort('NOT_FND', "Apptaggings for item %s for app %s not found" % (item.fqin,  app.fqin))
        return itemtagapps

    #######################################################################################################################
    #we have no web service based equivalents for this as yet: TODO. Thus
    #we shall still consider as internal

    def addItemType(self, currentuser, typespec):
        typespec=validatetypespec(typespec)
        authorize(False, self.whosdb, currentuser, currentuser)#any logged in user
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
        authorize(False, self.whosdb, currentuser, currentuser)#any logged in user
        permit(currentuser==itemtype.creator, "User %s not authorized." % currentuser.nick)
        self.session.delete(itemtype)
        return OK

    def addTagType(self, currentuser, typespec):
        typespec=validatetypespec(typespec, spectype="tagtype")
        authorize(False, self.whosdb, currentuser, currentuser)#any logged in user
        try:
            tagtype=TagType(**typespec)
        except:
            doabort('BAD_REQ', "Failed adding tagtype %s" % typespec['fqin'])
        self.session.add(tagtype)
        return tagtype

    def removeTagType(self, currentuser, fullyQualifiedTagType):
        tagtype=self.getTagType(currentuser, fullyQualifiedTagType)
        authorize(False, self.whosdb, currentuser, currentuser)#any logged in user
        permit(currentuser==tagtype.creator, "User %s not authorized" % currentuser.nick)
        self.session.delete(tagtype)
        return OK

    #######################################################################################################################

    #multiple postings by the same user, preventded at dbase level by having (i, u, g) id as primary key.
    #THIRD PARTY MASQUERADABLE(TPM) eg current user=oauthed web service acting as user.
    #if item does not exist this will fail.
    def postItemIntoGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName, tagmode=False):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        item=_item(currentuser, self, itemorfullyQualifiedItemName)
        grp=_group(currentuser, self.whosdb,  grouporfullyQualifiedGroupName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, grp)
        permit(self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s can post into it" % grp.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)

        try:
            newposting=self.getPostingInGroup(currentuser, useras, grp, item)
        except:
            try:
                print "CREATING NEW ITEMGROUP", grp.fqin, item.name
                newposting=ItemGroup(item=item, group=grp, user=useras, itemuri=item.uri, itemtype=item.itemtype)
                self.session.add(newposting)

            except:
                doabort('BAD_REQ', "Failed adding newposting of item %s into group %s." % (item.fqin, grp.fqin))
        personalfqgn=useras.nick+"/group:default"

        if grp.fqin!=personalfqgn:
            personalgrp=self.whosdb.getGroup(currentuser, personalfqgn)
            if item not in personalgrp.itemsposted:
                print "NOT IN PERSONAL GRP"
                self.postItemIntoGroup(currentuser, useras, personalgrp, item, tagmode)
                #self.commit() is this needed?
        else:
            #the only time we want to add an item to an app is when we put it in our personal group
            #if we do it for each group then we will not be unique
            #how will this work when we let groups subscribe to apps? TODO
            appstring=item.itemtype.app
            itemtypesapp=self.whosdb.getApp(currentuser, appstring)
            #every time an item is added to a group:add it to the app corresponding to the group
            #if multiple people do this wont we have multiple postings. But isnt this ok
            #IN LIEU OF ROUTING 
            #NOTE: we o it only in personal group (since this is alreay added) as otherwise we'd have to
            #assure idempotency for each group the user added the item to
            self.postItemIntoApp(currentuser, useras, itemtypesapp, item, tagmode)
        #is taggings, ensure they are posted into group too, personal or otherwise
        #BUG: need idempotenvy in taggings
        if tagmode:
            taggings=self.getTaggingsByItemAndUser(currentuser, useras, item)
            if grp.fqin!=personalfqgn: #trying to post to personal group, prevent!
                for itemtag in taggings:
                    self.postTaggingIntoGroupFromItemtag(currentuser, useras, grp, itemtag)

        return item

    def postItemPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagmode=False):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        item=self.postItemIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagmode)
        return item

    def removeItemFromGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName):
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        grp=_group(currentuser, self.whosdb,  grouporfullyQualifiedGroupName)
        postingtoremove=self.getPostingInGroup(currentuser, useras, grp, itemtoberemoved)
        authorize_context_owner(False, self.whosdb, currentuser, useras, grp)
        permit(useras==postingtoremove.user and self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s who posted this item can remove it from the group" % grp.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
        self.session.remove(postingtoremove)
        return OK

    def postItemIntoApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagmode=False):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        app=_app(currentuser, self.whosdb, apporfullyQualifiedAppName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, app)
        permit(self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s can post into it" % app.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)

        try:         
            newposting=self.getPostingInApp(currentuser, useras, app, item)
        except:
            try:
                print "CREATING ITEMAPP", app.fqin, item.name
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
        if tagmode:
            taggings=self.getTaggingsByItemAndUser(currentuser, useras, item)
            for itemtag in taggings:
                self.postTaggingIntoAppFromItemtag(currentuser, useras, app, itemtag)
        print "FINIAH APP POST"
        return item

    def removeItemFromApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName):
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        app=_app(currentuser, self.whosdb, apporfullyQualifiedAppName)
        postingtoremove=self.getPostingInApp(currentuser, useras, app, itemtoberemoved)
        authorize_context_owner(False, self.whosdb, currentuser, useras, app)
        permit(useras==postingtoremove.user and self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s who posted this item can remove it from the app" % app.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
        self.session.remove(postingtoremove)
        return OK

    #######################################################################################################################
    #Stuff for a single item
    #When a web service adds an item on their site, and we add it here as the web service user, do we save the item?
    #If we havent saved the item, can we post it to a group?: no Item id. Must we not make the web service save the
    #item first? YES. But there is no app. Aah this must be done outside in web service!!

    def saveItem(self, currentuser, useras, itemspec):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        authorize(False, self.whosdb, currentuser, useras)#sysadmin or any logged in user where but cu and ua must be same
        fqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, fqgn)
        itemspec['itemtype']=self.getItemType(currentuser, itemspec['itemtype'])
        itemspec=validatespec(itemspec)
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            print "was the item found?"
            newitem=self.getItem(currentuser, itemspec['fqin'])
        except:
            #the item was not found. Create it
            try:
                print "ITSPEC", itemspec
                newitem=Item(**itemspec)
                self.session.add(newitem)
                # print "Newitem is", newitem.info()
            except:
                # import sys
                # print sys.exc_info()
                doabort('BAD_REQ', "Failed adding item %s" % itemspec['fqin'])
        #self.session.add(newitem)
        #appstring=newitem.itemtype.app

        #print "APPSTRING\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\", appstring
        #itemtypesapp=self.whosdb.getApp(currentuser, appstring)
        tagmode=True
        self.postItemIntoGroup(currentuser, useras, personalgrp, newitem, tagmode)
        print '**********************'        
        #IN LIEU OF ROUTING
        #self.postItemIntoApp(currentuser, useras, itemtypesapp, newitem)
        #NOTE: above is now done via saving item into group, which means to say its auto done on personal group addition
        #But now idempotency, when I add it to various groups, dont want it to be added multiple times
        #thus we'll do it only when things are added to personal groups: which they always are
        print '&&&&&&&&&&&&&&&&&&&&&&', 'FINISHED SAVING'
        return newitem

    #deletion semantics with group user not clear at all! TODO: personal group removal only, item remains, are permits ok?
    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        authorize(False, self.whosdb, currentuser, useras)#sysadmin or any logged in user where but cu and ua must be same
        fqgn=useras.nick+"/group:default"
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
    # If tag exists we must use it instead of creating new tag: this is useful for rahuldave/tag:statistics
    #or rahuldave/tag:machinelearning. For notes, we expect an autogened name and we wont reuse that note
    #thus multiple names are avoided as each tag is new. But when tagging an item, make sure you are appropriately
    #creating a new tag or reusing an existing one. And that tag is uniqie to the user, so indeeed pavlos/tag:statistics
    #is different
    #what prevents me from using someone elses tag? validatespec DOES
    def tagItem(self, currentuser, useras, fullyQualifiedItemName, tagspec, tagmode=False):
        tagspec['tagtype']=self.getTagType(currentuser, tagspec['tagtype'])
        tagspec=validatespec(tagspec, spectype='tag')
        authorize(False, self.whosdb, currentuser, useras)
        print "FQIN", fullyQualifiedItemName
        itemtobetagged=self.getItem(currentuser, fullyQualifiedItemName)
        try:
            print "was tha tag found"
            tag=self.getTag(currentuser, tagspec['fqin'])
        except:
            #the tag was not found. Create it
            try:
                print "try creating tag"
                newtag=Tag(**tagspec)
                self.session.add(newtag)
            except:
                doabort('BAD_REQ', "Failed adding tag %s" % tagspec['fqin'])
        
        print "newtagging"
        try:
            print "was the itemtag found"
            itemtag=self.getTagging(currentuser, newtag, itemtobetagged)
        except:
            try:
                newtagging=ItemTag(itemtobetagged, newtag, useras)
            except:
                doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s" % (itemtobetagged.fqin, newtag.fqin))
        self.session.add(newtagging)
        personalfqgn=useras.nick+"/group:default"
        personalgrp=self.whosdb.getGroup(currentuser, personalfqgn)
        #Add tag to default personal group
        print "adding to %s" % personalgrp.fqin

        self.postTaggingIntoGroupFromItemtag(currentuser, useras, personalgrp, newtagging)
        #at this point it goes to the itemtypes app too.
        #This will get the personal, and since no commit, i think we will not hit personal. 
        #nevertheless we protect against it below
        if tagmode:
            groupsitemisin=itemtobetagged.get_groupsin(useras)
            #the groups user is in that item is in: in tagmode we make sure, whatever groups item is in, tags are in
            for grp in groupsitemisin:
                if grp.fqin!=personalfqgn:
                    #wont be added to app for these
                    self.postTaggingIntoGroupFromItemtag(currentuser, useras, grp, newtagging)
        #print itemtobetagged.itemtags, "WEE", newtag.taggeditems, newtagging.tagtype.name
        return newtag, newtagging

    def untagItem(self, currentuser, useras, fullyQualifiedTagName, fullyQualifiedItemName):
        #Do not remove item, do not remove tag, do not remove tagging
        #just remove the tag from the personal group
        authorize(False, self.whosdb, currentuser, useras)
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
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        grp=_group(currentuser, self.whosdb,  grouporfullyQualifiedGroupName)
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, grp)
        #The itemtag must exist at first
        #NOT ALLOWING USER TO POST SOMEONE ELSES TAGGING INTO GROUP. (What about someone else's tag? We could use this for tag subtypig)
        #YES.
        #this is opposed to other items, once found anywhere, can be posted into group
        itemtag=self.getTagging(currentuser, tag, item)
        permit(self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s can post into it" % grp.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into group %s" % grp.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
        print "ITEMTAG", itemtag, item, grp, tag
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            print "was the group ragging found"
            newitg=self.getGroupTagging(currentuser, itemtag=itemtag, group=grp)
        except:
            try:
                newitg=TagitemGroup(itemtag, grp, useras)
                self.session.add(newitg)
            except:
                doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in group %s" % (item.fqin, tag.fqin, grp.fqin))


        

        personalfqgn=useras.nick+"/group:default"
        #post item tagging to app only when we post tag to personal group. 
        #this way its only posted once
        if grp.fqin==personalfqgn:
            personalgrp=self.whosdb.getGroup(currentuser, personalfqgn)
            appstring=item.itemtype.app
            itemtypesapp=self.whosdb.getApp(currentuser, appstring)
            self.postTaggingIntoApp(currentuser, useras, itemtypesapp, item, tag)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return itemtag, newitg

    def postTaggingPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        return self.postTaggingIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName)

    #Is item in group? If not add it? depends on UI schemes
    def postTaggingIntoGroupFromItemtag(self, currentuser, useras, grouporfullyQualifiedGroupName, itemtag):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        grp=_group(currentuser, self.whosdb,  grouporfullyQualifiedGroupName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, grp)

        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        permit(self.whosdb.isMemberOfGroup(useras, grp),
            "Only member of group %s can post into it" % grp.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into group %s" % grp.fqin)
        #TODO: below tells us who can masquerade. thats about oauth or other 
        #authorization. But the context like grp is important. That an appowner
        #can masquerade the currentuser to be the groupowner must be expressed
        #elsewhere
        #so perhaps we need a routing structure for that. Keep this in mind
        # permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
        #      "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
        try:
            newitg=self.getGroupTagging(currentuser, itemtag=itemtag, group=grp)
        except:
            try:
                newitg=TagitemGroup(itemtag, grp, useras)
                self.session.add(newitg)
            except:
                doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in group %s" % (itemtag.item.fqin, tag.fqin, grp.fqin))

        

        personalfqgn=useras.nick+"/group:default"
        #only when we do post tagging to personal group do we post tagging to app. this ensures app dosent have multiples.
        if grp.fqin==personalfqgn:
            personalgrp=self.whosdb.getGroup(currentuser, personalfqgn)
            appstring=itemtag.item.itemtype.app
            itemtypesapp=self.whosdb.getApp(currentuser, appstring)
            self.postTaggingIntoAppFromItemtag(currentuser, useras, itemtypesapp, itemtag)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return newitg

    #BUG: currently not sure what the logic for everyone should be on this, or if it should even be supported
    #as other users have now seen stuff in the group. What happens to tagging. Leave alone for now.
    def removeTaggingFromGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        grp=_group(currentuser, self.whosdb,  grouporfullyQualifiedGroupName)
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, grp)
        #BUG: no other auths. But the model for this must be figured out.
        #The itemtag must exist at first
        itemtag=self.getTagging(currentuser, tag, item)
        itgtoberemoved=self.getGroupTagging(currentuser, itemtag, grp)
        self.session.remove(itgtoberemoved)
        return OK

    def postItemAndTaggingIntoGroup(self, currentuser, useras, grouporfullyQualifiedGroupName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        #I removed the above and didnt replace it by a simple authorize. part of the question is how authorizes
        #compound. In this case we want the ownership to be allowed but also need u to be a member. we could let it be checked
        #at the embedded funcs/
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        grp=_group(currentuser, self.whosdb,  grouporfullyQualifiedGroupName)
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        tagmode=False
        item=self.postItemIntoGroup(currentuser, useras, grp, item, tagmode)
        #at this point we have a tag not a existing tagging so we should let the tagmode be false.
        itemtag, itg = self.postTaggingIntoGroup(currentuser, useras, grp, item, tag)
        return item

    def postItemAndTaggingPublic(self, currentuser, useras, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        grp=self.whosdb.getGroup(currentuser, 'adsgut/group:public')
        return self.postItemAndTaggingIntoGroup(currentuser, useras, grp, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName)


    #NOTE: we are not requiring that item be posted into group or that tagging autopost it. FIXME. think we got this
    def postTaggingIntoAppFromItemtag(self, currentuser, useras, apporfullyQualifiedAppName, itemtag):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        app=_app(currentuser, self.whosdb, apporfullyQualifiedAppName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, app)

        #Note tagger need not be creator of item.

        permit(self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s can post into it" % app.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into app %s" % app.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)

        #The itemtag must exist at first
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            newita=self.getAppTagging(currentuser, itemtag=itemtag, application=app)
        except:
            try:
                newita=TagitemApplication(itemtag, app, useras)
                self.session.add(newita)
            except:
                doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in app %s" % (itemtag.item.fqin, tag.fqin, app.fqin))    
        
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return newita

    def postTaggingIntoApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        app=_app(currentuser, self.whosdb, apporfullyQualifiedAppName)
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, app)

        #Note tagger need not be creator of item.
        itemtag=self.getTagging(currentuser, tag, item)

        permit(self.whosdb.isMemberOfApp(useras, app),
            "Only member of app %s can post into it" % app.fqin)
        permit(useras==itemtag.user,
            "Only creator of tag can post into app %s" % app.fqin)
        # permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
        #     "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)

        #The itemtag must exist at first
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        try:
            newita=self.getAppTagging(currentuser, itemtag=itemtag, application=app)
        except:
            try:
                newita=TagitemApplication(itemtag, app, useras)
                self.session.add(newita)
            except:
                doabort('BAD_REQ', "Failed adding newtagging on item %s with tag %s in app %s" % (item.fqin, tag.fqin, app.fqin))    
        
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return itemtag, newita

    #BUG: currently not sure what the logic for everyone should be on this, or if it should even be supported
    #as other users have now seen stuff in the group. What happens to tagging. Leave alone for now.
    def removeTaggingFromApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        app=_app(currentuser, self.whosdb, apporfullyQualifiedAppName)
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        authorize_context_owner(False, self.whosdb, currentuser, useras, app)
        #BUG proper permitting to be worked out
        #The itemtag must exist at first
        itemtag=self.getTagging(currentuser, tag, item)
        itatoberemoved=self.getAppTagging(currentuser, itemtag, app)
        self.session.remove(itatoberemoved)
        return OK

    def postItemAndTaggingIntoApp(self, currentuser, useras, apporfullyQualifiedAppName, itemorfullyQualifiedItemName, tagorfullyQualifiedTagName):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        #again: just rely on permitting from embedded funcs?
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        app=_app(currentuser, self.whosdb, apporfullyQualifiedAppName)
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        tagmode=False
        item=self.postItemIntoApp(currentuser, useras, app, item, tagmode)
        itemtag, ita=self.postTaggingIntoApp(currentuser, useras, app, item, tag)
        return itemtag, ita
    #######################################################################################################################


    #######################################################################################################################

    #ALL KINDS OF GETS
    #are we impliciting that fqin be guessable? if we use a random, possibly not? BUG
    def getItemByFqin(self, currentuser, fullyQualifiedItemName):
        #fullyQualifiedItemName=nsuser.nick+"/"+itemname
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        authorize(False, self.whosdb, currentuser, currentuser)#as long as logged on
        try:
            item=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        except:
            doabort('AOK_REQ', "Item with name %s not found." % fullyQualifiedItemName)
        return item.info()

    #the uri can be saved my multiple users, which would give multiple results here. which user to use
    #should we not use useras. Ought we be getting from default group?
    #here I use useras, but suppose the useras is not the user himself or herself (ie currentuser !=useras)
    #then what? In other words if the currentuser is a group or app owner how should things be affected?
    #CURRENTLY DONT ALLOW THIS FUNC TO BE MASQUERADED.
    #We except, but send back a 200, so that a ads page can set that this item was never saved

    #so nor sure how useful as still comes from a users saving
    #BUG: or should we search by uri, no matter who has saved? The system wont allow an item to be created
    #more than once. but, wont uris be reused? unless insist on unique uris. Allowing uris to pick from name
    #we should be ok tho.
    def getItemByURI(self, currentuser, useras, itemuri):
        #permit(currentuser==useras or self.whosdb.isSystemUser(currentuser), "User %s not authorized or not systemuser" % currentuser.nick)
        authorize(False, self.whosdb, currentuser, currentuser)#as long as logged on, and currentuser=useras
        try:
            item=self.session.query(Item).filter_by(uri=itemuri, creator=useras).one()
        except:
            doabort('NOT_FND', "Item with uri %s not saved by %s." % (itemuri, useras.nick))
        return item.info()

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
            ciocoll=ItemGroup.group
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

    #remember this returns items in your personal group, not those created by you. Everytime
    #you post someone elses items into a group, it does get added to your personal group
    def getItems(self, currentuser, useras, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        userthere=False
        page=0
        paginate=20
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser,criteria['itemtype'])
        if criteria.has_key('userthere'):
            userthere=criteria.pop('userthere')
        if criteria.has_key('paginate'):
            paginate=criteria.pop('paginate')
        if criteria.has_key('page'):
            page=criteria.pop('page')
        #print "****************************PPPPPPP", context, fqin, criteria, userthere
        print "CRITERIS", criteria
        if context == None:
            if userthere:
                #permit(currentuser==useras, "Current user is not useras")
                authorize(False, self.whosdb, currentuser, useras)
                fqin=useras.nick+"/group:default"
                grp=self.whosdb.getGroup(currentuser, fqin)
                items,whenposteds=self._doItemFilter(context, useras, grp, ItemGroup, criteria, fvlist, orderer)
            else:
                #permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
                authorize(False, self.whosdb, currentuser, None)
                items, whenposteds = self._doItemFilter(context, None, None, None, criteria, fvlist, orderer)
            #permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
            #items, whenposteds = self._doItemFilter(context, None, None, None, criteria, fvlist, orderer)
        elif context == 'group':
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp), "Only member of group %s allowed" % grp.fqin)
            authorize_context_member(False, self.whosdb, currentuser, None, grp)
            # permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
            #     "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            #auth set up as member for currentuser or sysadmin as that includes owner and lets members
            #access each others stuff in a group context. useas is not needed as only currentuses who are members
            #alllowed in (besides sys) and once in, can filter at length.
            additional=['groupwhenposted']
            if userthere:
                items,whenposteds=self._doItemFilter(context, useras, grp, ItemGroup, criteria, fvlist, orderer, additional)
            else:
                items, whenposteds = self._doItemFilter(context, None, grp, ItemGroup, criteria, fvlist, orderer, additional)
        elif context == 'app':
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app), "Only member of app %s allowed" % app.fqin)
            authorize_context_member(False, self.whosdb, currentuser, None, app)
            # permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
            #     "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
            additional=['appwhenposted']
            if userthere:
                items,whenposteds=self._doItemFilter(context, useras, app, ItemApplication, criteria, fvlist, orderer, additional)
            else:
                items,whenposteds=self._doItemFilter(context, None, app, ItemApplication, criteria, fvlist, orderer, additional)

        eleinfo=[ele.info(useras) for ele in items]
        count=len(eleinfo)
        for i in range(count):
            if whenposteds[i]==None:
                eleinfo[i]['whenposted']=None
            else:
                eleinfo[i]['whenposted']=whenposteds[i].isoformat()

        return eleinfo, count



    
    #BUG: check for permitting bugs
    def _getTaggingsWithCriterion(self, currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer):
        userthere=False
        page=0
        paginate=20      
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.getTagType(currentuser, criteria['tagtype'])
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.getItemType(currentuser, criteria['itemtype'])
        if criteria.has_key('userthere'):
            userthere=criteria.pop('userthere')
        if criteria.has_key('paginate'):
            paginate=criteria.pop('paginate')
        if criteria.has_key('page'):
            paginate=criteria.pop('page')
        filterlist=[]
        print "CRITERIS", criteria
        if context==None:
            thechoice=ItemTag
            taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item))
            if userthere:
                #permit(currentuser==useras, "Current user is not useras")
                authorize(False, self.whosdb, currentuser, useras)
                taggings=taggings.filter(ItemTag.user==useras)
            else:
                authorize(False, self.whosdb, currentuser, None)
                #permit(self.whosdb.isSystemUser(currentuser), "Only System User allowed")
                #taggings=taggings
            additional=[]
        elif context=='group':
            thechoice=TagitemGroup         
            grp=self.whosdb.getGroup(currentuser, fqin)
            permit(self.whosdb.isMemberOfGroup(useras, grp), "Only member of group %s allowed" % grp.fqin)
            authorize_context_member(False, self.whosdb, currentuser, None, grp)
            # permit(currentuser==useras or self.whosdb.isOwnerOfGroup(currentuser, grp) or self.whosdb.isSystemUser(currentuser),
            #     "Current user must be useras or only owner of group %s or systemuser can masquerade as user" % grp.fqin)
            taggingothers=self.session.query(TagitemGroup).filter_by(group=grp)
            taggings=taggingothers.join(Item, TagitemGroup.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemGroup.user==useras)
            additional=['groupwhentagposted']
        elif context=='app':
            thechoice=TagitemApplication
            app=self.whosdb.getApp(currentuser, fqin)
            permit(self.whosdb.isMemberOfApp(useras, app), "Only member of app %s allowed" % app.fqin)
            authorize_context_member(False, self.whosdb, currentuser, None, app)
            # permit(currentuser==useras or self.whosdb.isOwnerOfApp(currentuser, app) or self.whosdb.isSystemUser(currentuser),
            #     "Current user must be useras or only owner of app %s or systemuser can masquerade as user" % app.fqin)
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
        tcounts={}

        #BUG: should we be iterating here? Isnt this information more easily findable?
        #but dosent that require replacing info by something more collection oriented?
        #permitting inside
        taggings=self._getTaggingsWithCriterion(currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer)
        for ele in taggings:
            eled=ele.info()#DONT pass useras as the tag class uses its own user to make sure security is not breached
            #print "eled", eled
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
                tcounts[eledfqin]=0
            titems[eledfqin].append(eled)
            tcounts[eledfqin]=tcounts[eledfqin]+1
        count=len(titems.keys())
        rhash.update({'taggings':titems, 'count':count, 'tagcounts':tcounts})
        return rhash

#should there be a getTagsForItemSpec

    def getItemsForTagspec(self, currentuser, useras, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        rhash={}
        titems={}
        #permitting inside
        taggings=self._getTaggingsWithCriterion(currentuser, useras, context, fqin, criteria, rhash, fvlist, orderer)

        #BUG: simplify and get counts? we should not be iterating before sending out as we are here. That will slow things down
        for ele in taggings:
            eled=ele.info()
            print "eled", eled['taginfo']
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=eled['iteminfo']
        count=len(titems.keys())
        rhash.update({'items':titems.values(), 'count':count})
        return rhash




    def getItemsForTag(self, currentuser, useras, tagorfullyQualifiedTagName, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        #in addition to whatever criteria (which ones are allowed ought to be in web service or here?) are speced
        #we need to get the tag
        rhash={}
        tag=_tag(currentuser, self,  tagorfullyQualifiedTagName)
        print "TAG", tag, tagorfullyQualifiedTagName
        #You would think that this ought to not be here because of the groups and apps, but remember, tags are specific
        #to users. Use the spec functions in this situation.
        permit(useras==tag.creator, "User must be creator of tag %s" % tag.fqin)
        criteria['tagtype']=tag.tagtype.fqin
        criteria['tagname']=tag.name
        #more detailed permitting inside: this is per user!
        rhash = self.getItemsForTagspec(currentuser, useras, context, fqin, criteria, fvlist, orderer)
        return rhash


    def getTagsForItem(self, currentuser, useras, itemorfullyQualifiedItemName, context=None, fqin=None, criteria={}, fvlist=[], orderer=[]):
        item=_item(currentuser, self,  itemorfullyQualifiedItemName)
        #BUG: whats the security I can see the item?
        criteria['name']=item.name
        criteria['itemtype']=item.itemtype.fqin
        #permitting inside but this is for multiple items
        rhash=self.getTaggingForItemspec(currentuser, useras, context, fqin, criteria, fvlist, orderer)
        return rhash

    #this one is to be used for autocompletes and stuff to have all the information show up at any given time
    #Do we need to have context and criteria?
    #it would seem tagtype is the only thing to support, as tags are orthogonal to groups and apps
    #in any case it would be easy to add it later, but the idea in this would be to bypass _getCriterion
    #and complex joins alltogether
    def getItemsorTagsCreatedByUser(self, currentuser, useras, fullyQualifiedItemType):
        if fullyQualifiedItemType:
            datype=self.getItemType(currentuser, fullyQualifiedItemType)
        else:
            datype=None
        authorize(False, self.whosdb, currentuser, useras)
        if datype:
            usersitems=useras.itemscreated.filter_by(itemtype=datype)
        else:
            usersitems=useras.itemscreated
        infos=[thing.info() for thing in usersitems]
        count=len(infos)
        print "===>>>", datype
        return infos, count, datype
#should there be a function to just return tags. Dont TODO we need funcs to return simple tagclouds and stuff?
#do this with the UI. The funcs do exist here as small getTagging funcs

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
    postdb.saveItem(currentuser, rahuldave, dict(name="hello kitty", itemtype="ads/pub", creator=rahuldave))
    #postdb.commit()
    postdb.saveItem(currentuser, rahuldave, dict(name="hello doggy", itemtype="ads/pub2", creator=rahuldave))
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
    #Wen a tagging is posted to a group, the item should be autoposted into there too 
    #NOTE: actually this is taken care of by posting into group on tagging, and making sure tags are posted
    #along with items into groups
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "ads/hello kitty")
    postdb.postItemIntoGroup(currentuser,rahuldave, "adsgut/group:public", "ads/hello kitty")#public post
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "ads/hello doggy")
    #TODO: below NOT NEEDED GOT FROM DEFAULT: SHOULD IT ERROR OUT GRACEFULLY OR BE IDEMPOTENT?
    #postdb.postItemIntoApp(currentuser,rahuldave, "ads/app:publications", "ads/hello doggy")
    print "PTGS"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello kitty", "rahuldave/ads/tag:stupid")
    print "1"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello kitty", "rahuldave/ads/tag:dumb")
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello doggy", "rahuldave/ads/tag:dumbdog")
    print "2"
    #bottom commented as now autoadded
    #postdb.postTaggingIntoApp(currentuser, rahuldave, "ads/app:publications", "ads/hello doggy", "rahuldave/ads/tag:dumbdog")
    print "HOOCH"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "ads/hello doggy", "rahuldave/ads/tag2:dumbdog2")
    #bottom commented as now autoadded
    #postdb.postTaggingIntoApp(currentuser, rahuldave, "ads/app:publications", "ads/hello doggy", "rahuldave/ads/tag2:dumbdog2")

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