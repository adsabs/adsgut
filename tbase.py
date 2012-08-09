from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import classes
from config import *
class TBase:   
    def setup(self):
        engine = create_engine('sqlite:///'+DBASE_FILE, convert_unicode=True)
        db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
        #engine = create_engine('sqlite:///:memory:', echo=False)
        #Session = sessionmaker(bind=engine)
        #self.session = Session()
        self.session=db_session
        # You probably need to create some tables and 
        # load some test data, do so here.

        # To create tables, you typically do:
        classes.DaBase.metadata.create_all(engine)

    def teardown(self):
        self.session.close()
