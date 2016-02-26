#!venv/bin/python
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from oauth import OAuthSignIn
import logging

app = Flask(__name__)
app.config.from_pyfile('../config.py')

db = SQLAlchemy(app)

lm = LoginManager(app)
lm.login_view = 'index'

handler = logging.FileHandler(app.config["LOG_FILENAME"])
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(app.config["LOG_FORMAT"]))
app.logger.addHandler(handler)

from views import *
