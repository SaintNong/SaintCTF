import sqlite3

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model, UserMixin):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer, nullable=True)

    def is_active(self):
        return True

    def __repr__(self):
        return f"<User '{self.uid}', '{self.username}', '{self.score}>"

    def get_id(self):
        return self.uid



