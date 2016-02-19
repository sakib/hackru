#!venv/bin/python
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from oauth import OAuthSignIn


app = Flask(__name__)
app.config.from_pyfile('../config.py')

db = SQLAlchemy(app)

lm = LoginManager(app)
lm.login_view = 'index'


from views import *
