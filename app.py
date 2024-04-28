import os

from flask import Flask, render_template
from challenges import ChallengeManager
from routes import register_routes
from constants import RESET_DATA

from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'password123'
    app.config['TEMPLATES_AUTO_RELOAD'] = True # https://stackoverflow.com/a/38371484

    # Extensions
    from models import db
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorised():
        return render_template('login.html', user=current_user, login_msg=True)

    bcrypt = Bcrypt()
    bcrypt.init_app(app)

    # Fake extension
    challenge_manager = ChallengeManager()

    # https://github.com/pallets/jinja/issues/1766
    @app.template_test("contains")
    def contains(seq, value):
        return value in seq

    # Register app routes
    register_routes(app, db, bcrypt, challenge_manager)

    # Reset the database if data reset flag is checked
    if RESET_DATA:
        with app.app_context():
            db.drop_all()
            db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')
