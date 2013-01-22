
"""
Configuration for all the blueprints that should be registered in the system
each tuple contains
1: the module where the blueprint is
2: blueprint name (note, the blueprints must be defined or imported in the __init__.py of each module
3: prefix for the application
"""

#blueprints from core module
from adsgut.modules import index

_BLUEPRINTS_CORE = [
    {'module':index, 'blueprint':'index_blueprint', 'prefix':''},
]

#blueprints from all other modules
from adsgut.modules import user, adsgut

_BLUEPRINTS_MODULES = [
    {'module':user, 'blueprint':'user_blueprint', 'prefix':'/user'},
    {'module':adsgut, 'blueprint':'adsgut_blueprint', 'prefix':'/adsgut' },
]


BLUEPRINTS = _BLUEPRINTS_CORE + _BLUEPRINTS_MODULES