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

    def postItemIntoGroup(self, currentuser, useras, fullyQualifiedGroupName, itemspec):
        itemspec['itemtype']=self.session.query(ItemType).filter_by(fqin=itemspec['itemtype']).one()
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newitem=Item(**validatespec(itemspec))
        self.session.add(newitem)
        grp.groupitems.append(newitem)
        return OK

    def removeItemFromGroup(self, currentuser, useras, fullyQualifiedGroupName, fullyQualifiedItemName):
        grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
        itemtoberemoved=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        itemtoberemoved.groupsin.remove(grp)
        return OK

    def tagItem(self, currentuser, useras, fullyQualifiedItemName, tagspec):
        tagspec['tagtype']=self.session.query(TagType).filter_by(fqin=tagspec['tagtype']).one()
        itemtobetagged=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newtag=Tag(**validatespec(tagspec, spectype='tag'))
        self.session.add(newtag)
        newtag.taggeditems.append(itemtobetagged)
        return OK

    def untagItem(self, currentuser, useras, fullyQualifiedTagName, fullyQualifiedItemName):
        itemtobeuntagged=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        tag=self.session.query(Tag).filter_by(fqin=fullyQualifiedTagName).one()
        itemtobeuntagged.itemtags.remove(tag)
        return OK

    def postItemIntoApp(self, currentuser, useras, fullyQualifiedAppName, itemspec):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        #Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
        newitem=Item(**validatespec(itemspec))
        self.session.add(newitem)
        app.appitems.append(newitem)
        return OK

    def removeItemFromApp(self, currentuser, useras, fullyQualifiedAppName, fullyQualifiedItemName):
        app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
        itemtoberemoved=self.session.query(Item).filter_by(fqin=fullyQualifiedItemName).one()
        itemtoberemoved.applicationsin.remove(app)
        return OK

    def saveItem(self, currentuser, useras, itemspec):
        fqgn=useras.nick+"/group:default"
        return self.postItemIntoGroup(currentuser, useras, fqgn, itemspec)

    def deleteItem(self, currentuser, useras, fullyQualifiedItemName):
        fqgn=useras.nick+"/group:default" #ALSO TRIGGER others (bug)
        return self.removeItemFromGroup(currentuser, useras, fqgn, fullyQualifiedItemName)



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
        #whosdb.edu()