DBASE_FILE="/tmp/adsgut.db"


APP_NAME="adsgutapp"
adsgut_blueprint=None
class AppConfig(object):
    #flask Setting for debug view in case of errors
    DEPLOYMENT_PATH = None
    DEBUG = False
    SECRET_KEY = 'SecretKeyForSessionSigning'
    #Flask setting for unittest
    TESTING = False
    #prints the template in the bottom of the page with the link to SOLR
    PRINT_DEBUG_TEMPLATE = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DBASE_FILE
    DATABASE_CONNECT_OPTIONS = {}
    APP_VERSION = '2013_01_07'
    MONGOALCHEMY_DATABASE = 'adsabs'
    MONGOALCHEMY_SERVER = 'localhost'
    MONGOALCHEMY_PORT = 27017
    MONGOALCHEMY_SAFE_SESSION = False

config=AppConfig