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

class TestClass1:   
    def setup(self):
        engine = create_engine('sqlite:///:memory:', echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        # You probably need to create some tables and 
        # load some test data, do so here.

        # To create tables, you typically do:
        DaBase.metadata.create_all(engine)

    def teardown(self):
        self.session.close()


    def test_something(self):
        sess=self.session
        adsgutuser=User(name='adsgut')
        adsuser=User(name='ads')
        sess.add(adsgutuser)
        sess.add(adsuser)
        sess.flush()