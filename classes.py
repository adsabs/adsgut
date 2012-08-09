#sqlalchemy setup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, mapper
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, text
from dbase import DaBase
#DaBase = declarative_base()

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

#Invites to applications are for betas. Invites to groups must be accepted to join
#so it depends on who the current user is: for apps its the adsgut user, for invites, its the user himself?
UserGroup = Table('user_group', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.group_id'))
)

InvitationGroup = Table('invitation_group', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.group_id')),
    Column('accepted', Boolean, default=False)
)

UserApplication = Table('user_application', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('application_id', Integer, ForeignKey('applications.application_id'))
)

InvitationApplication = Table('invitation_application', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('application_id', Integer, ForeignKey('applications.application_id')),
    Column('accepted', Boolean, default=True)
)

GroupApplication = Table('group_application', DaBase.metadata,
    Column('group_id', Integer, ForeignKey('groups.group_id')),
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

#  the group below is for groups, and apps. Posting too anything posts to users private group.
# so any in not starting with users private group lands up with a posting to users private group.
#How do we check against recursion? we must check to see (a) if reasoning payload has private group nothing needs be done
#(b) if reasoning payload dosent havee private check if item is in private and if not put it into private
#Now the access pubsubs will be triggered. We will (c) need to make sure we are not double posting using (user, item, group) tuple

#We will also need to create intype id's representing things like ads:all or all:all .
#Or should that column not be in intype id. I think intypes\#should be used. 
#Only apps need to define appnick:all

REASONINGS=[]

AccessTable = Table('accesstable', DaBase.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('intag_id', Integer, ForeignKey('tags.tag_id')),#includes apps. could this generally be used with tags?
    Column('intype_id', Integer, ForeignKey('itemtypes.id')),
    Column('outtag_id', Integer, ForeignKey('tags.tag_id')),
    Column('reasoning_id', Integer)
)

class User(DaBase):
    __tablename__='users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)
    nick = Column(String, unique=True, nullable=False)#expect unique
    email = Column(String, unique=True, nullable=False)#expect unique
    systemuser = Column(Boolean, default=False)
    groupsin = relationship('Group', secondary=UserGroup,
                            backref=backref('groupusers', lazy='dynamic'))
    groupsinvitedto = relationship('Group', secondary=InvitationGroup,
                            backref=backref('groupsinvitedusers', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=UserApplication,
                            backref=backref('applicationusers', lazy='dynamic'))
    applicationsinvitedto = relationship('Application', secondary=InvitationApplication,
                            backref=backref('applicationsinvitedusers', lazy='dynamic'))
    def __repr__(self):
        return "<User:%s:%s>" % (self.nick, self.email)

    def info(self):
        return {'name': self.name, 'nick': self.nick}

class ItemType(DaBase):
    __tablename__='itemtypes'
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    type=Column(String)
    fqin = Column(String, unique=True, nullable=False)
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
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    creator = relationship('User', backref=backref('itemscreated', lazy='dynamic'))
    name = Column(String, nullable=False)#this is the main text, eg for article, it could be title.
    #make it useful, make it searchable.
    fqin = Column(String, unique=True, nullable=False)
    uri = Column(String, unique=True)
    metajson = Column(Text)
    whencreated = Column(DateTime, server_default=text(THENOW))
    __mapper_args__ = {'polymorphic_on': 'type', 'polymorphic_identity': 'item'}
    groupsin = relationship('Group', secondary=ItemGroup,
                            backref=backref('groupitems', lazy='dynamic'))
    applicationsin = relationship('Application', secondary=ItemApplication,
                             backref=backref('applicationitems', lazy='dynamic'))

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
    #Description is the tagtext. along with the name, the description (arguments etc)
    #form the complete tag: tagtype:name, description
    description = Column(Text)
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
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lastupdated = Column(DateTime, server_default=text(THENOW))
    owner = relationship('User', primaryjoin='Group.owner_id == User.id', backref=backref('groupsowned', lazy='dynamic'))
    existence_public = Column(Boolean, default=False)
    personalgroup = Column(Boolean, default=False)
    appgroup = Column(Boolean, default=False)

    def __repr__(self):
        return "<Grp:%s,%s>" % (self.owner.nick, self.fqin)

    def info(self):
        #should return fully qualified name instead
        return {'name': self.name, 'description': self.description, 'owner': self.owner.nick, 'fqgn': self.fqin, 'creator': self.creator.nick, 'whencreated': self.whencreated.strftime("%Y-%m-%d %H:%M:%S")}

class Application(Group):
    __tablename__='applications'
    __mapper_args__ = {'polymorphic_identity': 'application', 'polymorphic_on': 'type'}
    application_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    #Not sure what the effect of having the column down there is.
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    #WONDER HOW BELOW WORKS. IF IT DOES
    owner = relationship('User', primaryjoin='Application.owner_id == User.id', backref=backref('appsowned', lazy='dynamic'))
    subscriptionjson = Column(Text, default="", nullable=False)

    def __repr__(self):
        return "<App:%s,%s>" % (self.owner.nick, self.fqin)

    def info(self):
        return {'name': self.name, 'description': self.description, 'owner': self.owner.nick, 'fqan': self.fqin, 'creator': self.creator.nick, 'whencreated': self.whencreated.strftime("%Y-%m-%d %H:%M:%S")}

Group.applicationsin = relationship('Application', secondary=GroupApplication, 
                            primaryjoin=GroupApplication.c.group_id == Group.group_id,
                            secondaryjoin=GroupApplication.c.application_id == Application.application_id,
                            backref=backref('applicationgroups', lazy='dynamic'))


if __name__=="__main__":
    from sqlalchemy import create_engine
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
    adsgutuser=User(nick='adsgut', email="adsgut@adslabs.org")
    adsuser=User(nick='ads', email="ads@adslabs.org")
    session.add(adsgutuser)
    session.add(adsuser)
    defaultgroup=Group(name='default', creator=adsgutuser, owner=adsgutuser, fqin="adsgut/default")
    session.add(defaultgroup)
    adspubsapp=Application(name='publications', creator=adsuser, owner=adsuser, fqin="ads/publications")
    session.add(adspubsapp)
    print "---------"
    pubtype=ItemType(name="pub", creator=adsuser, fqin="ads/pub")
    session.add(pubtype)
    notetype=TagType(name="note", creator=adsuser, fqin="ads/note")
    session.add(notetype)
    #session.commit()
    #pubtype=session.query(ItemType).filter_by(name="pub")[0]
    #print "PUBTYPE", pubtype
    #USERSET
    rahuldave=User(nick='rahuldave', email="rahuldave@gmail.com")
    rahuldave.groupsin.append(defaultgroup)
    session.add(rahuldave)
    jluker=User(nick='jluker', email="jluker@gmail.com")
    session.add(jluker)
    jluker.groupsin.append(defaultgroup)
    jluker.applicationsin.append(adspubsapp)
    #GROUPSET
    mlg=Group(name='ml', creator=rahuldave, owner=rahuldave, fqin="rahuldave/ml")
    session.add(mlg)
    thispub = Item(name="hello kitty", uri='xxxlm', itemtype=pubtype, creator=rahuldave, fqin="rahuldave/hello kitty")
    thistag = Tag(taggeditem=thispub, itemtype=notetype, tagtype=notetype, creator=rahuldave, name="crazy note", fqin="rahuldave/crazy note")
    
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