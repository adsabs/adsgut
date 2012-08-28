#from http://flask.pocoo.org/snippets/97/
#usage:
# @app.route("/test")
# def view():
#     abort(422, {'errors': dict(password="Wrong password")})
from werkzeug.exceptions import default_exceptions, HTTPException
from flask import make_response, abort as flask_abort, request
from flask.exceptions import JSONHTTPException

ADSGUT_AOK_REQ=200
ADSGUT_AOK_CRT=201
ADSGUT_BAD_REQ=400
ADSGUT_NOT_FND=404
ADSGUT_SRV_ERR=500
ADSGUT_SRV_UNA=503
ADSGUT_NOT_AUT=401
ADSGUT_FOR_BID=403

adsgut_errtypes=[
    ('ADSGUT_AOK_REQ',ADSGUT_AOK_REQ, 'Request Ok'),
    ('ADSGUT_AOK_CRT',ADSGUT_AOK_CRT, 'Object Created'),
    ('ADSGUT_BAD_REQ',ADSGUT_BAD_REQ, 'Bad Request'),
    ('ADSGUT_NOT_FND',ADSGUT_NOT_FND, 'Not Found'),
    ('ADSGUT_SRV_ERR',ADSGUT_SRV_ERR, 'Internal Server Error'),
    ('ADSGUT_SRV_UNA',ADSGUT_SRV_UNA, 'Service Unavailable'),
    ('ADSGUT_NOT_AUT', ADSGUT_NOT_AUT,'Not Authorized'),
    ('ADSGUT_FOR_BID',ADSGUT_FOR_BID, 'Forbidden'),
]

def abort(status_code, body=None, headers={}):
    """
    Content negiate the error response.

    """

    if 'text/html' in request.headers.get("Accept", ""):
        error_cls = HTTPException
    else:
        error_cls = JSONHTTPException
    #error_cls = JSONHTTPException
    class_name = error_cls.__name__
    bases = [error_cls]
    attributes = {'code': status_code}
    print default_exceptions
    if status_code in default_exceptions:
        # Mixin the Werkzeug exception
        bases.insert(0, default_exceptions[status_code])

    error_cls = type(class_name, tuple(bases), attributes)
    print "BODY", body, error_cls, bases
    errori=error_cls()
    if body==None:
        body={}
    errori=error_cls(dict(body, code=errori.code, error=errori.name))
    #This is just a hack to get the code and the name in currently
    flask_abort(make_response(errori, status_code, headers))

def doabort():
    pass