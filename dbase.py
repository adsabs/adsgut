from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DaBase = declarative_base()


#This gets called once. import the classes, then import this
def setup_db(dbfile):
    print "DBFILE IS", dbfile
    engine = create_engine('sqlite:///'+dbfile, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
    
    DaBase.query = db_session.query_property()
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #import yourapplication.models
    return engine, db_session

def init_db(engine):
    DaBase.metadata.create_all(bind=engine)


class Database(object):

    def __init__(self, session):
        self.session = session

    def commit(self):
        self.session.commit()

    def flush(self):
        self.session.flush()

    def remove(self):
    	self.session.remove()
