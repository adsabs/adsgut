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

def validatespec(specdict, spectype="item"):
    if spectype=="tag":
        specdict['fqin']=specdict['creator'].nick+"/"+specdict['tagtype'].fqin+":"+specdict['name']
    else:
        specdict['fqin']=specdict['creator'].nick+"/"+specdict['name']
    return specdict

def validatetypespec(specdict, spectype="itemtype"):
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

class Postdb(dbase.Database):

    def addItemType(self, currentuser, typespec):
        typespec=validatetypespec(typespec)
        itemtype=ItemType(**typespec)
        self.session.add(itemtype)
        return OK

    def removeItemType(self, currentuser, fullyQualifiedItemType):
        itemtype=self.session.query(ItemType).filter_by(fqin=fullyQualifiedItemType).one()
        self.session.delete(itemtype)
        return OK

    def addTagType(self, currentuser, typespec):
        typespec=validatetypespec(typespec, spectype="tagtype")
        tagtype=TagType(**typespec)
        self.session.add(tagtype)
        return OK

    def removeTagType(self, currentuser, fullyQualifiedTagType):
        itemtype=self.session.query(TagType).filter_by(fqin=fullyQualifiedTagType).one()
        self.session.delete(tagtype)
        return OK


    def tagItem(self, currentuser, useras, fullyQualifiedItemName, tagspec):
        tagspec['tagtype']=self.session.query(TagType).filter_by(fqin=tagspec['tagtype']).one()
        itemtobetagged=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newtag=Tag(**validatespec(tagspec, spectype='tag'))
        self.session.add(newtag)
        newtagging=ItemTag(item=itemtobetagged, tag=newtag, user=useras, 
            itemuri=itemtobetagged.uri, tagname=newtag.name, tagtype=tagspec['tagtype'], itemtype=itemtobetagged.itemtype)
        self.session.add(newtagging)
        self.commit()
        print "::", newtag.fqin
        fqgn=useras.nick+"/group:default"
        print "in tagItem", fqgn
        #Add tag to default personal group
        self.postTaggingIntoGroup(currentuser, useras, fqgn, fullyQualifiedItemName, newtag.fqin)
        #print itemtobetagged.itemtags, "WEE", newtag.taggeditems, newtagging.tagtype.name
        return OK

    def untagItem(self, currentuser, useras, fullyQualifiedTagName, fullyQualifiedItemName):
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        itemtobeuntagged=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        taggingtoremove=self.session.query(ItemTag).filter_by(tag=tag, item=itemtobeuntagged).one()
        self.session.remove(taggingtoremove)
        return OK

    def postItemIntoGroup(self, currentuser, useras, fullyQualifiedGroupName, itemspec):
        if type(itemspec) is types.StringType:
            newitem=self.session.query(Item).filter_by(fqin=itemspec).one()
        else:
            itemspec['itemtype']=self.session.query(ItemType).filter_by(fqin=itemspec['itemtype']).one()
            #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
            newitem=Item(**validatespec(itemspec))
            self.session.add(newitem)
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        newposting=ItemGroup(item=newitem, group=grp, user=useras, itemuri=newitem.uri, itemtype=newitem.itemtype)
        self.session.add(newposting)
        #self.commit()
        #print newitem.groupsin, "WEE", grp.itemsposted, newposting.itemtype.name
        #grp.groupitems.append(newitem)
        return OK

    def removeItemFromGroup(self, currentuser, useras, fullyQualifiedGroupName, fullyQualifiedItemName):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        itemtoberemoved=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        postingtoremove=self.session.query(ItemGroup).filter_by(group=grp, item=itemtoberemoved).one()
        self.session.remove(postingtoremove)
        return OK

    def postItemIntoApp(self, currentuser, useras, fullyQualifiedAppName, itemspec):
        if type(itemspec) is types.StringType:
            newitem=self.session.query(Item).filter_by(fqin=itemspec).one()
        else:
            itemspec['itemtype']=self.session.query(ItemType).filter_by(fqin=itemspec['itemtype']).one()
            #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
            newitem=Item(**validatespec(itemspec))
            self.session.add(newitem)
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        newposting=ItemApplication(item=newitem, application=app, user=useras, itemuri=newitem.uri, itemtype=newitem.itemtype)
        self.session.add(newposting)
        #self.commit()
        #print newitem.groupsin, "WEE", grp.itemsposted
        #grp.groupitems.append(newitem)
        return OK

    def removeItemFromApp(self, currentuser, useras, fullyQualifiedAppName, fullyQualifiedItemName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        itemtoberemoved=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        postingtoremove=self.session.query(ItemApplication).filter_by(application=app, item=itemtoberemoved).one()
        self.session.remove(postingtoremove)
        return OK


    def postTaggingIntoGroup(self, currentuser, useras, fullyQualifiedGroupName, fullyQualifiedItemName, fullyQualifiedTagName):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        #The itemtag must exist at first
        itemtag=self.session.query(ItemTag).filter_by(item=itm, tag=tag).one()
        #print "ITEMTAG", itemtag
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newitg=TagitemGroup(itemtag=itemtag, group=grp, tagname=tag.name, tagtype=tag.tagtype, user=useras)
        self.session.add(newitg)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return OK

    def removeTaggingFromGroup(self, currentuser, useras, fullyQualifiedGroupName, fullyQualifiedItemName, fullyQualifiedTagName):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        #The itemtag must exist at first
        itemtag=self.session.query(ItemTag).filter_by(item=itm, tag=tag).one()
        itgtoberemoved=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        self.session.remove(itgtoberemoved)
        return OK

    def postTaggingIntoApp(self, currentuser, useras, fullyQualifiedAppName, fullyQualifiedItemName, fullyQualifiedTagName):
        app=self.session.query(Group).filter_by(fqin=fullyQualifiedAppName).one()
        itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        #The itemtag must exist at first
        itemtag=self.session.query(ItemTag).filter_by(item=itm, tag=tag).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newita=TagitemApplication(itemtag=itemtag, application=app, tagname=tag.name, tagtype=tag.tagtype, user=useras)
        self.session.add(newita)
        #grp.groupitems.append(newitem)
        # self.commit()
        # print itemtag.groupsin, 'jee', grp.itemtags
        # itgto=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, group=grp).one()
        # print itgto
        return OK

    def removeTaggingFromApp(self, currentuser, useras, fullyQualifiedAppName, fullyQualifiedItemName, fullyQualifiedTagName):
        app=self.session.query(Group).filter_by(fqin=fullyQualifiedAppName).one()
        itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        #The itemtag must exist at first
        itemtag=self.session.query(ItemTag).filter_by(item=itm, tag=tag).one()
        itatoberemoved=self.session.query(TagitemApplication).filter_by(itemtag=itemtag, application=app).one()
        self.session.remove(itatoberemoved)
        return OK

    #######################################################################################################################
    #Stuff for a single item

    def saveItem(self, currentuser, useras, itemspec):
        fqgn=useras.nick+"/group:default"
        print "in saveItem", fqgn
        return self.postItemIntoGroup(currentuser, useras, fqgn, itemspec)

    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        fqgn=useras.nick+"/group:default" #ALSO TRIGGER others (bug)
        return self.removeItemFromGroup(currentuser, useras, fqgn, fullyQualifiedItemName)

    def getItemByName(self, currentuser, useras, itemname):
        fullyQualifiedItemName=useras.nick+"/"+itemname
        try:
            itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        except:
            doabort(404, "Item with name %s not saved by %s." % (fullyQualifiedItemName, useras.nick))
        return itm.info()

    #the uri can be saved my multiple users, which would give multiple results here. which user to use
    #should we not use useras. Ought we be getting from default group?
    #here I use useras, but suppose the useras is not the user himself or herself (ie currentuser !=useras)
    #then what? In other words if the currentuser is a group or app owner how should things be affected?
    def getItemByURI(self, currentuser, useras, itemuri):
        try:
            itm=self.session.query(Item).filter_by(uri=itemuri, creator=useras).one()
        except:
            doabort(404, "Item with uri %s not saved by %s." % (itemuri, useras.nick))
        return itm.info()

    #######################################################################################################################

    def getItems(self, currentuser, useras, context=None, fqin=None, criteria={}):
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.session.query(ItemType).filter_by(fqin=criteria['itemtype']).one()      
        if context == None:
            items=self.session.query(Item).filter_by(**criteria)
        elif context == 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            items=self.session.query(Item).select_from(join(Item, ItemGroup))\
                            .filter(ItemGroup.group==grp)\
                            .filter_by(**criteria)
        elif context == 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
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
            criteria['itemtype']=self.session.query(ItemType).filter_by(fqin=criteria['itemtype']).one()
        if context == None:
            grp=self.session.query(Group).filter_by(fqin=useras.nick+"/group:default").one()
            items=self.session.query(Item).select_from(join(Item, ItemGroup))\
                                        .filter(ItemGroup.group==grp)\
                                        .filter_by(**criteria)
        elif context=='group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            items=self.session.query(Item).select_from(join(Item, ItemGroup))\
                                        .filter(ItemGroup.user==useras, ItemGroup.group==grp)\
                                        .filter_by(**criteria)
        elif context=='app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            items=self.session.query(Item).select_from(join(Item, ItemApplication))\
                                        .filter(ItemApplication.user==useras, ItemApplication.application==app)\
                                        .filter_by(**criteria)
        return [ele.info() for ele in items]

    #we're going through tagitem group and tagitemapp. Not sure this is the best choice.
    def getTagging(self, currentuser, useras, context=None, fqin=None, criteria={}):
        rhash={}
        titems={}
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
        if context==None:
            taggings=self.session.query(ItemTag).filter_by(**criteria)
        elif context=='group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            #taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(user=useras, group=grp)]
            taggings=self.session.query(TagitemGroup)\
                                        .filter_by(group=grp)\
                                        .filter_by(**criteria)
            rhash['group']=grp.fqin
        elif context=='app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            #taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(user=useras, application=app)]
            taggings=self.session.query(TagitemApplication)\
                                        .filter_by(application=app)\
                                        .filter_by(**criteria)
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'taggings':titems})
        return rhash

    def getTaggingForUser(self, currentuser, useras, context=None, fqin=None, criteria={}):
        rhash={}
        titems={}
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
        if context==None:
            taggings=self.session.query(ItemTag).filter_by(user=useras).filter_by(**criteria)
        elif context=='group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            #taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(user=useras, group=grp)]
            taggings=self.session.query(TagitemGroup)\
                                        .filter_by(user=useras, group=grp)\
                                        .filter_by(**criteria)
            rhash['group']=grp.fqin
        elif context=='app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            #taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(user=useras, application=app)]
            taggings=self.session.query(TagitemApplication)\
                                        .filter_by(user=useras, application=app)\
                                        .filter_by(**criteria)
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash

    #Leave it be right now because we are running out of time
    def getItemsForTag(self, currentuser, useras, fullyQualifiedTagName, context=None, fqin=None):
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        if context is None:           
            items=tag.taggeditems
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            #bottom could be done as query on the assoc-proxy collection too! Is that more idiomatic? BUG (Could also be faster)
            #more likely somewhere else
            items=[ele.item for ele in self.session.query(TagitemGroup).filter_by(tag=tag, group=grp)]
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            items=[ele.item for ele in self.session.query(TagitemApplication).filter_by(tag=tag, application=app)]
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

    def getItemsForTagspec(self, currentuser, useras, context=None, fqin=None, criteria={}):
        rhash={}
        titems={}
        itemtype=None
        userthere=False
        print "CRI", criteria
        itemselections={'itemname':'name', 'itemuri': 'uri', 'itemtype': 'itemtype'}
        tagselections={'tagname':'tagname', 'tagtype': 'tagtype'}
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.session.query(ItemType).filter_by(fqin=criteria['itemtype']).one()
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
        if context==None:
            taggings = self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter_by(**tagcriteria)
            if userthere:
                taggings=taggings.filter(ItemTag.user==useras)
        elif context=='group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            taggingothers=self.session.query(TagitemGroup).filter_by(group=grp).filter_by(**tagcriteria)
            rhash['group']=grp.fqin
            taggings=taggingothers.join(Item, TagitemGroup.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemGroup.user==useras)
        elif context=='app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            taggingothers=self.session.query(TagitemApplication).filter_by(application=app).filter_by(**tagcriteria)
            rhash['app']=app.fqin
            taggings=taggingothers.join(Item, TagitemApplication.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemApplication.user==useras)
        if userthere:
            rhash['user']=useras.nick
        if itemtype:
            print taggings.all()
            taggings=taggings.filter(Item.itemtype==itemtype)
            print taggings.all(), itemtype.fqin
        if itemsql:
            taggings=taggings.filter(itemsql)

        #Perhaps fluff this up with tags in a reasonable way! TODO
        for ele in taggings:
            eled=ele.info()
            #print "eled", eled
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=eled['iteminfo']
        rhash.update({'items':titems.values()})
        return rhash

    #BUG: cant we use more direct collections in the simple cases?
    def getTagsForItem(self, currentuser, useras, fullyQualifiedItemName, context=None, fqin=None, criteria={}):
        item=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
        rhash={}
        titems={}
        if context==None:
            taggings=self.session.query(ItemTag).filter_by(item=item).filter_by(**criteria)
        elif context=='group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            taggings=self.session.query(TagitemGroup).filter(TagitemGroup.item_id==item.id, TagitemGroup.group==grp).filter_by(**criteria)
            rhash['group']=grp.fqin
        elif context=='app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            taggings=self.session.query(TagitemApplication).filter(TagitemApplication.item_id==item.id, TagitemApplication.application==app).filter_by(**criteria)
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash


    def getTaggingForItemspec(self, currentuser, useras, context=None, fqin=None, criteria={}):
        rhash={}
        titems={}
        itemtype=None
        userthere=False       
        itemselections={'itemname':'name', 'itemuri': 'uri', 'itemtype': 'itemtype'}
        tagselections={'tagname':'tagname', 'tagtype': 'tagtype'}
        if criteria.has_key('tagtype'):
            criteria['tagtype']=self.session.query(TagType).filter_by(fqin=criteria['tagtype']).one()
        if criteria.has_key('itemtype'):
            criteria['itemtype']=self.session.query(ItemType).filter_by(fqin=criteria['itemtype']).one()
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
        print 'CRITERIA2', criteria, itemcriteria,tagcriteria, itemtype
        itemsql=_critsqlmaker(itemcriteria)
        print 'ITEMSQL', itemsql, tagcriteria, itemcriteria, criteria
        if context==None:
            taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter_by(**tagcriteria)
            if userthere:
                taggings=taggings.filter(ItemTag.user==useras)
        elif context=='group':            
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            print "Group", grp
            print "grp.itemtags", grp.itemtags.all()
            #alia=aliased(ItemTag, grp.itemtags)
            #taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter_by(group=grp).filter_by(**tagcriteria)
            #taggings=self.session.query().join(Item).filter_by(**tagcriteria)
            
            taggingothers=self.session.query(TagitemGroup).filter_by(group=grp).filter_by(**tagcriteria)
            #print taggingothers, [ele for ele in taggingothers.all()]
            #            .filter_by(**tagcriteria)
            rhash['group']=grp.fqin
            taggings=taggingothers.join(Item, TagitemGroup.item_id==Item.id)
            if userthere:
                taggings=taggings.filter(TagitemGroup.user==useras)

            #print "TAGG", taggings
        elif context=='app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
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
        for ele in taggings:
            eled=ele.info()
            #print "eled", eled
            eledfqin=eled['item']
            if not titems.has_key(eledfqin):
                titems[eledfqin]=[]
            titems[eledfqin].append(eled)
        rhash.update({'taggings':titems})
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
            uri='xxxlm', itemtype="ads/pub", creator=rahuldave, fqin="rahuldave/hello kitty"))
    postdb.saveItem(currentuser, rahuldave, dict(name="hello doggy", 
            uri='xxxlm-d', itemtype="ads/pub2", creator=rahuldave))
    postdb.commit()
    print "here"
    postdb.tagItem(currentuser, rahuldave, "rahuldave/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="stupid"))
    print "W++++++++++++++++++"
    postdb.tagItem(currentuser, rahuldave, "rahuldave/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="dumb"))
    postdb.tagItem(currentuser, rahuldave, "rahuldave/hello doggy", dict(tagtype="ads/tag", creator=rahuldave, name="dumbdog"))
    postdb.tagItem(currentuser, rahuldave, "rahuldave/hello doggy", dict(tagtype="ads/tag2", creator=rahuldave, name="dumbdog2"))
    postdb.commit()
    print "LALALALALA"
    #Wen a tagging is posted to a group, the item should be autoposted into there too BUG NOT ONE NOW
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty")
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "rahuldave/hello doggy")
    postdb.postItemIntoApp(currentuser,rahuldave, "ads/app:publications", "rahuldave/hello doggy")
    print "PTGS"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty", "rahuldave/ads/tag:stupid")
    print "1"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty", "rahuldave/ads/tag:dumb")
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello doggy", "rahuldave/ads/tag:dumbdog")
    print "2"
    postdb.postTaggingIntoApp(currentuser, rahuldave, "ads/app:publications", "rahuldave/hello doggy", "rahuldave/ads/tag:dumbdog")
    print "HOOCH"
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello doggy", "rahuldave/ads/tag2:dumbdog2")
    postdb.postTaggingIntoApp(currentuser, rahuldave, "ads/app:publications", "rahuldave/hello doggy", "rahuldave/ads/tag2:dumbdog2")

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