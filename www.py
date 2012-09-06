
from flask import Flask
import sys
import whosflask

app = Flask(__name__)

app.register_blueprint(whosflask.adsgut, url_prefix='/adsgut')

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__=='__main__':
    
    app.debug=True
    app.run()