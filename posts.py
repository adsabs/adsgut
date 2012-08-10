from classes import *
from whos import Whosdb, initialize_application
import tbase
import dbase
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
OK=200

#pubsub to be used in conjunction with the access table to get stuff into all groups.
#remember to have a proper exception mechanism

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
        itemspec['itemtype']=self.session.query(ItemType).filter_by(fqin=itemspec['itemtype']).one()
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newitem=Item(**validatespec(itemspec))
        self.session.add(newitem)
        newposting=ItemGroup(item=newitem, group=grp, user=useras, itemuri=newitem.uri, itemtype=itemspec['itemtype'])
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
        itemspec['itemtype']=self.session.query(ItemType).filter_by(fqin=itemspec['itemtype']).one()
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newitem=Item(**validatespec(itemspec))
        self.session.add(newitem)
        newposting=ItemApplication(item=newitem, application=app, user=useras, itemuri=newitem.uri, itemtype=itemspec['itemtype'])
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
        itatoberemoved=self.session.query(TagitemGroup).filter_by(itemtag=itemtag, application=app).one()
        self.session.remove(itatoberemoved)
        return OK

    def saveItem(self, currentuser, useras, itemspec):
        fqgn=useras.nick+"/group:default"
        return self.postItemIntoGroup(currentuser, useras, fqgn, itemspec)

    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        fqgn=useras.nick+"/group:default" #ALSO TRIGGER others (bug)
        return self.removeItemFromGroup(currentuser, useras, fqgn, fullyQualifiedItemName)

    def getTaggingForUser(self, currentuser, useras, context=None, fqin=None):
        pass

    def getItemsForUser(self, currentuser, useras, context=None, fqin=None):
        pass

    def getItemsForGroup(self, currentuser, useras, fullyQualifiedGroupName):
        pass

    def getTaggingForGroup(self, currentuser, useras, fullyQualifiedGroupName):
        pass

    def getItemsForApp(self, currentuser, useras, fullyQualifiedAppName):
        pass

    def getTaggingForApp(self, currentuser, useras, fullyQualifiedAppName):
        pass

    def getItemsForTag(self, currentuser, useras, fullyQualifiedTagName, context=None, fqin=None):
        pass

    def getItemsForTagName(self, currentuser, useras, tagname, context=None, fqin=None):
        pass



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
        postdb.postTaggingIntoGroup(currentuser, rahuldave, "rahuldave/group:ml", "rahuldave/hello kitty", "rahuldave/stupid paper")
        postdb.commit()
        #whosdb.edu()