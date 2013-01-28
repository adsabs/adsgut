# -*- coding: utf-8 -*-

import os
import sys

import tempfile
import subprocess
import logging

from flask.ext.script import Manager, Command, prompt, prompt_choices, prompt_bool #@UnresolvedImport

from adsgut import create_app
from config import config

config.LOGGING_CONFIG = None
logging.basicConfig(format='%(message)s', level=logging.INFO)

app = create_app(config)
manager = Manager(app)#, with_default_commands=False)

log = logging.getLogger("shell")


if __name__ == "__main__":
    manager.run()
