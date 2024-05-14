import os
import constants
import secrets

from flask import Flask, render_template, url_for
from challenges import ChallengeManager, time_ago

from routes import register_routes

from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt


def load_secret_key():
    # Check if a secret key was already generated
    if not os.path.isfile(constants.SECRET_KEY_FILE):
        print("No secret key file found, generating...")
        # Generate a secret key and store it in the file
        with open(constants.SECRET_KEY_FILE, "w") as file:
            secret = secrets.token_hex(64)
            file.write(secret)

    # Read the secret key from file
    with open(constants.SECRET_KEY_FILE, "r") as file:
        secret = file.read().strip()
        return secret


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.root_path, "database.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = load_secret_key()
    app.config["TEMPLATES_AUTO_RELOAD"] = True  # https://stackoverflow.com/a/38371484
    app.config["RESET_DATA"] = False

    # Extensions
    from models import db

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User, Solve  # Solve is used when the db is reset

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorised():
        return render_template("login.html", user=current_user, login_msg=True)

    bcrypt = Bcrypt()
    bcrypt.init_app(app)

    # Fake extension
    challenge_manager = ChallengeManager(app)

    # https://flask.palletsprojects.com/en/3.0.x/templating/#registering-filters
    app.jinja_env.filters["time_ago"] = time_ago

    # Register app routes
    register_routes(app, db, bcrypt, challenge_manager)

    # Reset the database if data reset flag is checked
    with app.app_context():
        if app.config["RESET_DATA"]:
            print("RESETTING DATABASE")
            print(
                "To keep database data through multiple runtimes, set RESET_DATA to False."
            )
            db.drop_all()

        db.create_all()
        db.session.commit()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0")
