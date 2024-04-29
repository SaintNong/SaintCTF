from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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


class Solve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=False)
    challenge_id = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=datetime.now)  # Who cares about UTC, this isn't a global CTF

    user = db.relationship('User', backref=db.backref('solves', lazy=True))

    def __repr__(self):
        return f'<Solve user={self.user.username} challenge_id={self.challenge_id} time={self.time}>'
