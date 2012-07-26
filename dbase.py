from config import *
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('sqlite:///'+DBASE_FILE, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
DaBase = declarative_base()
DaBase.query = db_session.query_property()

#This gets called once. import the classes, then import this
def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #import yourapplication.models
    DaBase.metadata.create_all(bind=engine)


class Database:

    def __init__(self, session):
        self.session = session

    def commit(self):
        self.session.commit()

    def flush(self):
        self.session.flush()

    def remove(self):
    	self.session.remove()
