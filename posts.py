from classes import *
import tbase
import dbase
#wont worry about permissions right now
#wont worry about cascade deletion right now either.
#what about permissions? MUCH LATER
#FUNDAMENTAL
OK=200

#pubsub to be used in conjunction with the access table to get stuff into all groups.

def validatespec(specdict, spectype):
    return specdict

class Postdb(dbase.Database):

    def postItemIntoGroup(self, currentuser, useras, fullyQualifiedGroupName, itemspec):
    	grp=self.session.query(Group).filter_by(fqin=fullyQualifiedGroupName).one()
    	#Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
    	newitem=Item(**validatespec(itemspec))
    	self.session.add(newitem)
    	grp.groupitems.append(newitem)
        return OK

    def postItemIntoApp(self, currentuser, useras, fullyQualifiedAppName, itemspec):
    	app=self.session.query(Application).filter_by(fqin=fullyQualifiedAppName).one()
    	#Information about user useras goes as namespace into newitem, but should somehow also be in main lookup table
    	newitem=Item(**validatespec(itemspec))
    	self.session.add(newitem)
    	app.appitems.append(newitem)
        return OK

     def saveItem(self. currentuser, useras, itemspec):
     	fqgn=useras.nick+"/group:default"
     	return self.postItemIntoGroup(currentuser, useras, fqgn, itemspec)