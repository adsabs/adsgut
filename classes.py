#sqlalchemy setup

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
DaBase = declarative_base()

#redis setup

#in mem setup
#our clases
#Base=object


#NO SECURITY and PERMISSIONS right now

ItemTag = Table('item_tag', DaBase.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('tag_id', Integer, ForeignKey('tags.tag_id'))
)

UserGroup = Table('user_group', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.group_id'))
)

UserApplication = Table('user_application', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('application_id', Integer, ForeignKey('applications.application_id'))
)

class User(DaBase):
    __tablename__='users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)
    email = Column(String)#expect unique
    groupsin = relationship('Group', secondary=UserGroup,
                            backref=backref('groupusers', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=UserApplication,
                            backref=backref('appusers', lazy='dynamic'))

class Item(DaBase):
    __tablename__='items'
    __mapper_args__ = {'polymorphic_identity': 'item','polymorphic_on': 'itemtype'}
    id = Column(Integer, primary_key=True)
    itemtype = Column(Integer, ForeignKey('itemtypes.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    uri = Column(String)
    metajson = Column(Text)
    whencreated = Column(DateTime)
    tags = relationship('Tag', secondary=ItemTag,
                            backref=backref('items', lazy='dynamic'))


class ItemType(DaBase):
    __tablename__='itemtypes'
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    description = Column(Text)
    whencreated = Column(DateTime)
    creator = relationship('User', backref=backref('itemtypes', lazy='dynamic'))

class Tag(Item):
    __tablename__='tags'
    __mapper_args__ = {'polymorphic_identity': 'tag', 'polymorphic_on': 'tagtype'}
    tag_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'))
    tagtype = Column(Integer, ForeignKey('tagtypes.tagtype_id'))
    tagtext = Column(Text)
    tagvisibility = Column(Boolean)
    

#bug: cant figure how to inherit this from itemtype
class TagType(DaBase):
    __tablename__='tagtypes'
    tagtype_id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    description = Column(Text)
    whencreated = Column(DateTime)
    tagtypemeta = Column(Text)
    creator = relationship('User', backref=backref('tagtypes', lazy='dynamic'))


class Group(Tag):
    __tablename__='groups'
    __mapper_args__ = {'polymorphic_identity': 'group'}
    group_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.tag_id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    lastupdated = Column(DateTime)
    owner = relationship('User', backref=backref('groupsowned', lazy='dynamic'))

class Application(Group):
    __tablename__='applications'
    __mapper_args__ = {'polymorphic_identity': 'application'}
    application_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    applmeta = Column(Text)
    #owner = relationship('User', backref=backref('appsowned', lazy='dynamic'))



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

if __name__=="__main__":
    engine = create_engine('sqlite:///:memory:', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    print DaBase.metadata.create_all(engine) 
    # User.add(User("rahuldave@gmail.com"))
    # for x in User.__theset__:
    #   print x.email
    # print TagType("rahuldave@gmail.com/comment").scope
    # Item.add(Item())
    # print Item.__theset__, Item.__thelist__, "lll", DaBase.__theset__
    adsgutuser=User(name='adsgut')
    adsuser=User(name='ads')
    session.add(adsgutuser)
    session.add(adsuser)
    defaultgroup=Group(name='default', owner=adsgutuser)
    session.add(defaultgroup)
    adspubsapp=Application(name='publications', owner=adsuser)
    session.add(adspubsapp)
    pubtype=ItemType(name="pub", creator=adsuser)
    session.add(pubtype)
    notetype=TagType(name="note", creator=adsuser)
    session.add(notetype)

    #USERSET
    rahuldave=User(name='rahuldave')
    session.add(rahuldave)
    jluker=User(name='jluker')
    session.add(jluker)

    #GROUPSET
    mlg=Group(name='ml', owner=rahuldave)
    session.add(mlg)

    session.commit()
    print session.query(User, User.name).all()
    print session.query(Group, Group.name).all()
    print session.query(Application, Application.name).all()
    print session.query(Item, Item.name).all()
    print session.query(ItemType, ItemType.name).all()
    print session.query(TagType, TagType.name).all()

    #Add users to group and app