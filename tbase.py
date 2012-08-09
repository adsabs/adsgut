from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
DBASE_FILE=":memory:"
import dbase
import classes
class TBase:   
    def setup(self):
        
        #engine = create_engine('sqlite:///:memory:', echo=False)
        #Session = sessionmaker(bind=engine)
        #self.session = Session()
        engine, self.session=dbase.setup_db(DBASE_FILE)
        # You probably need to create some tables and 
        # load some test data, do so here.

        # To create tables, you typically do:
        classes.DaBase.metadata.create_all(engine)

    def teardown(self):
        self.session.close()
