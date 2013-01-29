from flask import (Blueprint, request, flash, redirect,
                   url_for, render_template)

import logging

# For import *
__all__ = ['adsgut_blueprint']
#definition of the blueprint for the user part
adsgut_blueprint = Blueprint('adsgut', __name__, template_folder="templates", static_folder="static")

log = logging.getLogger(__name__)
