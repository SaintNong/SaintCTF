#    SaintCTF: A custom platform for hosting capture the flag tournaments.
#    Copyright (C) 2024  Ning Xiaozhou, Alex Dennis, Andrew Trang
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime
import os
import secrets
import logging
import os

import tomlkit
from flask import Flask, flash, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

import constants
from challenges import ChallengeManager, time_ago, challenge_anchor_id
from routes import register_routes


def load_secret(app):
    try:
        # Load the secret key from file
        with app.open_instance_resource(constants.SECRET_KEY_FILE, "r") as secrets_file:
            secret = secrets_file.read()

    except FileNotFoundError:
        # If the secret key does not exist, we create one
        with app.open_instance_resource(constants.SECRET_KEY_FILE, "w") as secrets_file:
            secret = secrets.token_hex(64)
            secrets_file.write(secret)

    return secret


def get_default_config():
    default_config = {
        "SQLALCHEMY_DATABASE_URI": {
            "default": "sqlite:///database.db",
            "comment": "The SQLAlchemy database URL.",
        },
        "CTF_START_TIME": {
            "default": datetime.datetime.now().isoformat(),
            "comment": "The start time for this event, in ISO 8601 format",
        },
        "FORCE_DISABLE_DOCKER": {
            "default": False,
            "comment": "Option to forcibly disable docker containerized challenges",
        },
        "RESET_DATABASE": {
            "default": False,
            "comment": "Option to reset the database when the server is started.",
        },
    }
    document = tomlkit.document()

    for option, data in default_config.items():
        default_value = data.get("default")
        comment = tomlkit.comment(data.get("comment"))

        document.add(comment)
        document[option] = default_value

    return document


def validate_config(config):
    keys = [
        "SQLALCHEMY_DATABASE_URI",
        "CTF_START_TIME",
        "FORCE_DISABLE_DOCKER",
        "RESET_DATABASE",
    ]

    for key in keys:
        if key not in config:
            raise KeyError(f"Option {key} was not found in configuration file")


def load_config_file(app, config_path):
    try:
        with app.open_instance_resource(config_path, "r") as config_file:
            document = tomlkit.parse(config_file.read())
        app.logger.info(f"Configuration file '{config_path}' was read.")
    except FileNotFoundError:
        document = get_default_config()
        with app.open_instance_resource(config_path, "w") as config_file:
            tomlkit.dump(document, config_file)
        app.logger.warning(f"Configuration file '{config_path}' was autogenerated.")

    validate_config(document)
    return document


def create_app():
    app = Flask(__name__, template_folder="templates")

    os.makedirs(
        app.instance_path, exist_ok=True
    )  # Ensure that the instance folder exists

    app.config["SECRET_KEY"] = load_secret(app)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True  # https://stackoverflow.com/a/38371484
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

    config = load_config_file(app, constants.CONFIG_FILE)
    app.config.update(config)

    app.logger.setLevel(logging.DEBUG)

    # Extensions
    from models import db

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    @login_manager.unauthorized_handler
    def unauthorised():
        flash("You have to log in to do that!")
        return redirect(url_for("login"))

    bcrypt = Bcrypt()
    bcrypt.init_app(app)

    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # Fake extension
    challenge_manager = ChallengeManager(app)

    # https://flask.palletsprojects.com/en/3.0.x/templating/#registering-filters
    app.jinja_env.filters["time_ago"] = time_ago
    app.jinja_env.filters["challenge_anchor_id"] = challenge_anchor_id

    # Register app routes
    register_routes(app, db, bcrypt, challenge_manager, csrf)

    # Reset the database if data reset flag is checked
    with app.app_context():
        if app.config["RESET_DATABASE"]:
            app.logger.warning("Database was reset")
            app.logger.warning(
                "To keep database data through multiple runtimes, set RESET_DATA to false in config.toml"
            )
            db.drop_all()

        db.create_all()
        db.session.commit()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0")
