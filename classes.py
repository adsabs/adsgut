#sqlalchemy setup

# import sqlalchemy
# from sqlalchemy import create_engine
# engine = create_engine('sqlite:///:memory:', echo=True)
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, String
# Base = declarative_base()

#redis setup

#in mem setup
#our clases
Base=object


#NO SECURITY and PERMISSIONS right now

class DaBase(object):
	__theset__ = set()

	@classmethod
	def add(cls, theobject):
		cls.__theset__.add(theobject)

class User(DaBase):
	def __init__(self, email):
		self.email = email

class Item(DaBase):
	__thelist__ = []

	@classmethod
	def add(cls, theobject):
		print "supercls", type(super(cls))
		super(Item,cls).add(theobject)
		cls.__thelist__.append(theobject)

class ItemType(DaBase):
	
	def __init__(self, itemtype):
		self.itemtype = itemtype
		self.scope, self.rawtype = self.itemtype.split('/')
		print "Hi"

class Tag(Item):
	pass

class TagType(ItemType):
	pass

class Group(Tag):
	pass

class Application(Group):
	pass

if __name__=="__main__":
	User.add(User("rahuldave@gmail.com"))
	for x in User.__theset__:
		print x.email
	print TagType("rahuldave@gmail.com/comment").scope
	Item.add(Item())
	print Item.__theset__, Item.__thelist__