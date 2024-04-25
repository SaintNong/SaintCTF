import os

from flask import Flask, request, jsonify, render_template, send_from_directory
from challenges import ChallengeManager
from routes import register_routes

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'password123'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)
challenge_manager = ChallengeManager()
register_routes(app, db, bcrypt, challenge_manager)


class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<User '{self.user_id}', '{self.username}', '{self.score}>"

    def get_id(self):
        return self.uid


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


if __name__ == '__main__':
    app.run()
