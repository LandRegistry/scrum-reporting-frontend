from application import db
from flask.ext.login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'scrum-users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
