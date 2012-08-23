from classes import *
from whos import Whosdb, initialize_application
import tbase
import dbase
import types
import config
from sqlalchemy.orm import join
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
OK=200

#pubsub to be used in conjunction with the access table to get stuff into all groups.
#remember to have a proper exception mechanism
#BUG: Rrewrite this whole file TO UE JOINS SIMPLY

def validatespec(specdict, spectype="item"):
    specdict['fqin']=specdict['creator'].nick+"/"+specdict['name']
    return specdict

def validatetypespec(specdict, spectype="itemtype"):
    specdict['fqin']=specdict['creator'].nick+"/"+specdict['name']
    return specdict

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
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newitg=TagitemGroup(itemtag=itemtag, group=grp, tagname=tag.name, user=useras)
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
        newita=TagitemApplication(itemtag=itemtag, application=app, tagname=tag.name, user=useras)
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

    def saveItem(self, currentuser, useras, itemspec):
        fqgn=useras.nick+"/group:default"
        print "in saveItem", fqgn
        return self.postItemIntoGroup(currentuser, useras, fqgn, itemspec)

    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        fqgn=useras.nick+"/group:default" #ALSO TRIGGER others (bug)
        return self.removeItemFromGroup(currentuser, useras, fqgn, fullyQualifiedItemName)

    def getItemByName(self, currentuser, useras, itemname):
        fullyQualifiedItemName=useras.nick+"/"+itemname
        itm=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        return itm.info()

    #the uri can be saved my multiple users, which would give multiple results here. which user to use
    #should we not use useras. Ought we be getting from default group?
    #here I use useras, but suppose the useras is not the user himself or herself (ie currentuser !=useras)
    #then what? In other words if the currentuser is a group or app owner how should things be affected?
    def getItemByURI(self, currentuser, useras, itemuri):
        itm=self.session.query(Item).filter_by(uri=itemuri, creator=useras).one()
        return itm.info()

    def getTaggingForUser(self, currentuser, useras, context=None, fqin=None):
        rhash={}
        titems={}
        if context is None:
            taggings=self.session.query(ItemTag).filter_by(user=useras)
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(user=useras, group=grp)]
            rhash['group']=grp.fqin
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(user=useras, application=app)]
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            if not titems.has_key(ele.item.fqin):
                titems[ele.item.fqin]=[]
            titems[ele.item.fqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash

    

    def getItemsForGroup(self, currentuser, useras, fullyQualifiedGroupName):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        return [ele.info() for ele in grp.itemsposted]

    def getItemsForUser(self, currentuser, useras, context=None, fqin=None):
        if context is None:
            grp=self.session.query(Group).filter_by(fqin=useras.nick+"/group:default").one()
            items=grp.itemsposted
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            items=[ele.item for ele in self.session.query(ItemGroup).filter_by(user=useras, group=grp)]
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            items=[ele.item for ele in self.session.query(ItemApplication).filter_by(user=useras, application=app)]
        return [ele.info() for ele in items]

    def getTaggingForGroup(self, currentuser, useras, fullyQualifiedGroupName):
        rhash={}
        titems={}
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(group=grp)]
        rhash['group']=grp.fqin

        for ele in taggings:
            eled=ele.info()
            if not titems.has_key(ele.item.fqin):
                titems[ele.item.fqin]=[]
            titems[ele.item.fqin].append(eled)
        rhash.update({'taggings':titems})
        return rhash

    def getItemsForApp(self, currentuser, useras, fullyQualifiedAppName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        return [ele.info() for ele in app.itemsposted]

    def getTaggingForApp(self, currentuser, useras, fullyQualifiedAppName):
        rhash={}
        titems={}
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(application=app)]
        rhash['group']=app.fqin

        for ele in taggings:
            eled=ele.info()
            if not titems.has_key(ele.item.fqin):
                titems[ele.item.fqin]=[]
            titems[ele.item.fqin].append(eled)
        rhash.update({'taggings':titems})
        return rhash

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
    def getItemsForTagname(self, currentuser, useras, tagname, context=None, fqin=None):
        tags=self.session.query(Tag).filter_by(name=tagname).all()
        if context is None:
            itemsnested = [tag.taggeditems for tag in tags]
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            itemsnested=[]
            for tag in tags:
                itemsnested.append([ele.item for ele in self.session.query(TagitemGroup).filter_by(tag=tag, group=grp)])
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            itemsnested=[]
            for tag in tags:
                itemsnested.append([ele.item for ele in self.session.query(TagitemApplication).filter_by(tag=tag, application=app)])
        
        items = [inner for outer in itemsnested for inner in outer]
        return [ele.info() for ele in items]
   

    def getItemsForItemname(self, currentuser, useras, itemname, context=None, fqin=None):        
        if context is None:
            items=self.session.query(Item).filter_by(name=itemname).all()
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            items=self.session.query(Item).select_from(join(Item, ItemGroup)).filter(ItemGroup.group==grp).filter(Item.name==itemname).all()
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            items=self.session.query(Item).select_from(join(Item, ItemApplication)).filter(ItemApplication.application==app).filter(Item.name==itemname).all()
        return [ele.info() for ele in items]

    def getItemsForTagtype(self, currentuser, useras, tagtypefqin, context=None, fqin=None):
        tagtypeobject=self.session.query(Tagtype).filter_by(fqin=tagtypefqin).one()
        tags=self.session.query(Tag).filter_by(tagtype=tagtypeobject).all()
        if context is None:
            itemsnested = [tag.taggeditems for tag in tags]
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            itemsnested=[]
            for tag in tags:
                itemsnested.append([ele.item for ele in self.session.query(TagitemGroup).filter_by(tag=tag, group=grp)])
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            itemsnested=[]
            for tag in tags:
                itemsnested.append([ele.item for ele in self.session.query(TagitemApplication).filter_by(tag=tag, application=app)])
        
        items = [inner for outer in itemsnested for inner in outer]
        return [ele.info() for ele in items]

    def getTagsForItem(self, currentuser, useras, fullyQualifiedItemName, context=None, fqin=None):
        item=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        rhash={}
        titems={}
        if context is None:
            taggings=self.session.query(ItemTag).filter_by(item=item)
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).filter_by(TagitemGroup.item_id==item.id, group=grp)]
            rhash['group']=grp.fqin
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).filter_by(TagitemApplication.item_id==item.id, application=app)]
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            if not titems.has_key(ele.item.fqin):
                titems[ele.item.fqin]=[]
            titems[ele.item.fqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash

    def getTagsForItemuri(self, currentuser, useras, itemuri, context=None, fqin=None):
        rhash={}
        titems={}
        if context is None:
            taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter_by(Item.uri==itemuri).all()
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).select_from(join(TagitemGroup, Item)).filter_by(Item.uri==itemuri,TagitemGroup.group=grp)]
            rhash['group']=grp.fqin
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).select_from(join(TagitemApplication, Item)).filter_by(Item.uri==itemuri,TagitemApplication.application=app)]
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            if not titems.has_key(ele.item.fqin):
                titems[ele.item.fqin]=[]
            titems[ele.item.fqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash

    def getTagsForItemtype(self, currentuser, useras, itemtypefqin, context=None, fqin=None):
        itemtypeobject=self.session.query(Itemtype).filter_by(fqin=itemtypefqin).one()
        rhash={}
        titems={}
        if context is None:
            taggings=self.session.query(ItemTag).select_from(join(ItemTag, Item)).filter_by(Item.itemtype==itemtypeobject).all()
        elif context is 'group':
            grp=self.session.query(Group).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemGroup).select_from(join(TagitemGroup, Item)).filter_by(Item.itemtype==itemtypeobject,TagitemGroup.group=grp)]
            rhash['group']=grp.fqin
        elif context is 'app':
            app=self.session.query(Application).filter_by(fqin=fqin).one()
            taggings=[ele.itemtag for ele in self.session.query(TagitemApplication).select_from(join(TagitemApplication, Item)).filter_by(Item.itemtype==itemtypeobject,TagitemApplication.application=app)]
            rhash['app']=app.fqin
        for ele in taggings:
            eled=ele.info()
            if not titems.has_key(ele.item.fqin):
                titems[ele.item.fqin]=[]
            titems[ele.item.fqin].append(eled)
        rhash.update({'user':useras.nick, 'taggings':titems})
        return rhash


def initialize_application(sess):
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
    postdb.saveItem(currentuser, rahuldave, dict(name="hello kitty", 
            uri='xxxlm', itemtype="ads/pub", creator=rahuldave, fqin="rahuldave/hello kitty"))
    postdb.commit()
    postdb.tagItem(currentuser, rahuldave, "rahuldave/hello kitty", dict(tagtype="ads/tag", creator=rahuldave, name="stupid paper"))
    postdb.commit()
    #Wen a tagging is posted to a group, the item should be autoposted into there too BUG NOT ONE NOW
    postdb.postItemIntoGroup(currentuser,rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty")
    postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty", "rahuldave/stupid paper")
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