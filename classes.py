#sqlalchemy setup

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, text
DaBase = declarative_base()

#redis setup

#in mem setup
#our clases
#Base=object
sqlite_NOW="CURRENT_TIMESTAMP"
THENOW=sqlite_NOW
#NO SECURITY and PERMISSIONS right now

# ItemTag = Table('item_tag', DaBase.metadata,
#     Column('item_id', Integer, ForeignKey('items.id')),
#     Column('tag_id', Integer, ForeignKey('tags.tag_id'))
# )

UserGroup = Table('user_group', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.group_id'))
)

UserApplication = Table('user_application', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('application_id', Integer, ForeignKey('applications.application_id'))
)

GroupApplication = Table('group_application', DaBase.metadata,
    Column('group_id', Integer, ForeignKey('users.id')),
    Column('application_id', Integer, ForeignKey('applications.application_id'))
)

ItemGroup = Table('item_group', DaBase.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('group_id', Integer, ForeignKey('groups.group_id'))
)

ItemApplication = Table('item_application', DaBase.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('application_id', Integer, ForeignKey('applications.application_id'))
)

TagGroup = Table('tag_group', DaBase.metadata,
    Column('tag_id', Integer, ForeignKey('tags.tag_id')),
    Column('group_id', Integer, ForeignKey('groups.group_id'))
)

TagApplication = Table('tag_application', DaBase.metadata,
    Column('tag_id', Integer, ForeignKey('tags.tag_id')),
    Column('application_id', Integer, ForeignKey('applications.application_id'))
)

class User(DaBase):
    __tablename__='users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    password = Column(String)
    email = Column(String, unique=True, nullable=False)#expect unique
    groupsin = relationship('Group', secondary=UserGroup,
                            backref=backref('groupusers', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=UserApplication,
                            backref=backref('applicationusers', lazy='dynamic'))

    def __repr__(self):
        return "<User:%s:%s>" % (self.name, self.email)

    def info(self):
        return {'name': self.name}

class ItemType(DaBase):
    __tablename__='itemtypes'
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    type=Column(String)
    description = Column(Text)
    whencreated = Column(DateTime, server_default=text(THENOW))
    creator = relationship('User', backref=backref('itemtypes', lazy='dynamic'))
    __mapper_args__ = {'polymorphic_identity': 'itemtype', 'polymorphic_on': 'type'}

#bug: cant figure how to inherit this from itemtype
class TagType(ItemType):
    __tablename__='tagtypes'
    #__mapper_args__ = {'polymorphic_on': 'name'}
    tagtype_id = Column(Integer, primary_key=True)
    itemtype_id = Column(Integer, ForeignKey('itemtypes.id'))
    __mapper_args__ = {'polymorphic_identity': 'tagtype', 'polymorphic_on': 'type'}

class Item(DaBase):
    __tablename__='items'
    id = Column(Integer, primary_key=True)
    itemtype_id = Column(Integer, ForeignKey('itemtypes.id'))
    itemtype = relationship('ItemType', primaryjoin=itemtype_id == ItemType.id, backref=backref('itemsofthistype', lazy='dynamic'))
    #itemtype_string = Column(String, ForeignKey('itemtypes.name'))
    type=Column(String)
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship('User', backref=backref('itemscreated', lazy='dynamic'))
    name = Column(String)#this is the main text, eg for article, it could be title.
    #make it seful, make it searchable.
    uri = Column(String, unique=True)
    metajson = Column(Text)
    whencreated = Column(DateTime, server_default=text(THENOW))
    __mapper_args__ = {'polymorphic_on': 'type', 'polymorphic_identity': 'item'}
    groupsin = relationship('Group', secondary=ItemGroup,
                            backref=backref('groupitems', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=ItemApplication,
                            backref=backref('applicationitems', lazy='dynamic'))
    #tags = relationship('Tag', secondary=ItemTag,
    #                        backref=backref('items', lazy='dynamic'))

    def __repr__(self):
        return "<Item:%s,%s>" % (self.itemtype.name, self.name)




class Tag(Item):
    __tablename__='tags'
    tag_id = Column(Integer, primary_key=True)
    #the item corresponding to tis tag, not the item tagged
    item_id = Column(Integer, ForeignKey('items.id'))
    taggeditem_id = Column(Integer, ForeignKey('items.id'))
    tagtype_id = Column(Integer, ForeignKey('tagtypes.tagtype_id'))
    tagtype = relationship('TagType', backref=backref('tagsofthistype', lazy='dynamic'))
    #is above redundant with itemtype?
    tagtext = Column(Text)
    taggeditem=relationship("Item", primaryjoin=taggeditem_id == Item.id, 
        backref=backref('tags', lazy='dynamic'))
    groupsin = relationship('Group', secondary=TagGroup,
                            backref=backref('grouptags', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=TagApplication,
                            backref=backref('applicationtags', lazy='dynamic'))
    __mapper_args__ = {'polymorphic_on': 'type', 'polymorphic_identity': 'tag', 'inherit_condition':Item.id==item_id}

    def __repr__(self):
        return "<Tag:%s,%s>" % (self.tagtype.name, self.name)


    #how to get a direct REL to items tagged thus? (see backref under items)
    #BELOW is not needed as the tag itself is posted into a group or not, separate from the item
    #tagvisibility = Column(Boolean, default=False)
    #OK Constructor to make some restrictions from the item class...how do we do this?
    #truth is I do not know
    
#bug: cant figure how to inherit this from itemtype
# class TagType(DaBase):
#     __tablename__='tagtypes'
#     tagtype_id = Column(Integer, primary_key=True)
#     creator_id = Column(Integer, ForeignKey('users.id'))
#     name = Column(String)
#     description = Column(Text)
#     whencreated = Column(DateTime, server_default=text(THENOW))
#     tagtypemeta = Column(Text)
#     creator = relationship('User', backref=backref('tagtypes', lazy='dynamic'))



class Group(Tag):
    __tablename__='groups'
    __mapper_args__ = {'polymorphic_identity': 'group', 'polymorphic_on': 'type'}
    group_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.tag_id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    lastupdated = Column(DateTime, server_default=text(THENOW))
    owner = relationship('User', primaryjoin='Group.owner_id == User.id', backref=backref('groupsowned', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=UserApplication,
                            backref=backref('applicationgroups', lazy='dynamic'))
    def __repr__(self):
        return "<Grp:%s,%s>" % (self.owner.name, self.name)

    def info(self):
        #should return fully qualified name instead
        return {'name': self.name}

class Application(Group):
    __tablename__='applications'
    __mapper_args__ = {'polymorphic_identity': 'application', 'polymorphic_on': 'type'}
    application_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    owner = relationship('User', primaryjoin='Application.owner_id == User.id', backref=backref('appsowned', lazy='dynamic'))

    def __repr__(self):
        return "<App:%s,%s>" % (self.owner.name, self.name)

    def info(self):
        return {'name': self.name}

class Database:

    def __init__(self, session):
        self.session = session

    def commit(self):
        self.session.commit()



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
    adsgutuser=User(name='adsgut', email="adsgut@adslabs.org")
    adsuser=User(name='ads', email="ads@adslabs.org")
    session.add(adsgutuser)
    session.add(adsuser)
    defaultgroup=Group(name='default', owner=adsgutuser)
    session.add(defaultgroup)
    adspubsapp=Application(name='publications', owner=adsuser)
    session.add(adspubsapp)
    print "---------"
    pubtype=ItemType(name="pub", creator=adsuser)
    session.add(pubtype)
    notetype=TagType(name="note", creator=adsuser)
    session.add(notetype)
    #session.commit()
    #pubtype=session.query(ItemType).filter_by(name="pub")[0]
    #print "PUBTYPE", pubtype
    #USERSET
    rahuldave=User(name='rahuldave', email="rahuldave@gmail.com")
    rahuldave.groupsin.append(defaultgroup)
    session.add(rahuldave)
    jluker=User(name='jluker', email="jluker@gmail.com")
    session.add(jluker)
    jluker.groupsin.append(defaultgroup)
    jluker.applicationsin.append(adspubsapp)
    #GROUPSET
    mlg=Group(name='ml', owner=rahuldave)
    session.add(mlg)
    thispub = Item(name="hello kitty", uri='xxxlm', itemtype=pubtype, creator=rahuldave)
    thistag = Tag(taggeditem=thispub, itemtype=notetype, tagtype=notetype, creator=rahuldave, name="crazy note")
    
    thispub.groupsin.append(mlg)
    thistag.groupsin.append(mlg)

    thispub.applicationsin.append(adspubsapp)
    thistag.applicationsin.append(adspubsapp)

    session.add(thispub)
    session.add(thistag)
    # print "----+"
    # thispub.tags.append(mlg)
    # thistag.tags.append(mlg)
    # print "+----"
    #dosent work under current model as each tag attaches to one item only, ie its not many-many
    session.commit()
    print "USERS",session.query(User, User.name).all()
    print "GROUPS",session.query(Group, Group.name).all()
    print "APPS",session.query(Application, Application.name).all()
    print "Items",session.query(Item, Item.name).all()
    print "Tags",session.query(Tag, Tag.name).all()
    print "Itemtypes",session.query(ItemType, ItemType.name).all()
    print "Tagtypes",session.query(TagType, TagType.name).all()
    print '------------'
    print "alltags:", thispub.tags.all(), "??", "note gives only tags"
    print "MLG:", mlg.groupitems.all(), mlg.grouptags.all()
    print "ADSPUBAPP:", adspubsapp.applicationitems.all(), adspubsapp.applicationtags.all()
    print "DEFGRPUSERS:", defaultgroup.groupusers.all()
    print "PUBAPPUSERS:", adspubsapp.applicationusers.all()

    #Add users to group and app