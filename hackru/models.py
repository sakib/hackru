#!venv/bin/python
from hackru import db
from flask.ext.login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # From MLH
    mlh_id = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), default=None)
    # For us
    github = db.Column(db.String(64), default=None)
    resume = db.Column(db.String(256), default=None)
    comments = db.Column(db.String(256), default=None)
    is_admin = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Integer, default=0)
      # 0 for Pre-Registered
      # 1 for Registered but not Confirmed
      # 2 for Confirmed Attendance
