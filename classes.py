#sqlalchemy setup

import sqlalchemy
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
DaBase = declarative_base()

#redis setup

#in mem setup
#our clases
#Base=object


#NO SECURITY and PERMISSIONS right now



class User(DaBase):
	__tablename__='users'
	id = Column(Integer, primary_key=True)
	nickname = Column(String)
	fullname = Column(String)
	password = Column(String)
	email = Column(String)
	groups = relationship('Group', backref="dauser")
	applications = relationship('Application', backref="dauser")

class Item(DaBase):
	__tablename__='items'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	name = Column(String)
	uri = Column(String)
	metajson = Column(Text)
	whencreated = Column(DateTime)
	tags = relationship('Tag', backref="daitem")


class ItemType(DaBase):
	__tablename__='itemtypes'
	id = Column(Integer, primary_key=True)
	creator_id = Column(Integer, ForeignKey('users.id'))
	name = Column(String)
	description = Column(Text)
	whencreated = Column(DateTime)

class Tag(Item):
	__tablename__='tags'
	__mapper_args__ = {'polymorphic_identity': 'tag'}
	tag_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
	tagtype = Column(Integer, ForeignKey('tagtypes.tagtype_id'))
	tagtext = Column(Text)
	tagvisibility = Column(Boolean)
	

class TagType(ItemType):
	__tablename__='tagtypes'
	tagtype_id = Column(Integer, ForeignKey('itemtypes.id'), primary_key=True)

class Group(Tag):
	__tablename__='groups'
	group_id = Column(Integer, ForeignKey('tags.tag_id'), primary_key=True)
	owner_id = Column(Integer, ForeignKey('users.id'))
	lastupdated = Column(DateTime)

class Application(Group):
	__tablename__='applications'
	application_id = Column(Integer, ForeignKey('groups.group_id'), primary_key=True)

# class ItemTag(DaBase):
# 	pass

# class UserGroup(ItemTag):
# 	pass

# class UserApplication(UserGroup):
# 	pass	

if __name__=="__main__":
	print DaBase.metadata.create_all(engine) 
	# User.add(User("rahuldave@gmail.com"))
	# for x in User.__theset__:
	# 	print x.email
	# print TagType("rahuldave@gmail.com/comment").scope
	# Item.add(Item())
	# print Item.__theset__, Item.__thelist__, "lll", DaBase.__theset__