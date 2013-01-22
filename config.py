DBASE_FILE="/tmp/adsgut.db"


APP_NAME-"adsgutapp"

class AppConfig(object):
    #flask Setting for debug view in case of errors
    DEBUG = False
    #Flask setting for unittest
    TESTING = False
    #prints the template in the bottom of the page with the link to SOLR
    PRINT_DEBUG_TEMPLATE = False

    APP_VERSION = '2013_01_07'

config=AppConfig