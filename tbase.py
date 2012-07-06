import classes
class TBase:   
    def setup(self):
        engine = classes.create_engine('sqlite:///:memory:', echo=False)
        Session = classes.sessionmaker(bind=engine)
        self.session = Session()
        # You probably need to create some tables and 
        # load some test data, do so here.

        # To create tables, you typically do:
        classes.DaBase.metadata.create_all(engine)

    def teardown(self):
        self.session.close()
