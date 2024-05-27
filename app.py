import datetime
import secrets

import tomlkit
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

import constants
from challenges import ChallengeManager, time_ago
from routes import register_routes


def load_config_file(config_path):
    default_options = {
        "RESET_DATABASE": False,
        "START_TIME": datetime.datetime.utcnow().isoformat(),
    }

    # Read the existing configuration or create a new file
    try:
        with open(config_path, "r") as config_file:
            config_file = tomlkit.parse(config_file.read())
    except FileNotFoundError:
        config_file = tomlkit.document()
    modified = False

    # Ensure all required options are present
    for section, options in default_options.items():
        # Check each section
        if section not in config_file:
            config_file[section] = tomlkit.table()
            modified = True

        for key, value in options.items():
            # Check every key of config file, filling it with the default value if it isn't present
            if key not in config_file[section]:
                config_file[section][key] = value
                modified = True

    # Write configuration changes
    if modified:
        with open(config_path, "w") as file:
            tomlkit.dump(config_file, file)

    # Flatten for config
    config = {
        key: value
        for section, data in config_file.items()
        for key, value in data.items()
    }

    return config


def create_app():
    app = Flask(__name__, template_folder="templates")
    config = load_config_file(constants.CONFIG_FILE)
    app.config.update(config)

    # Extensions
    from models import db

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User  # Solve is used when the db is reset

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorised():
        return render_template("login.html", user=current_user, login_msg=True)

    bcrypt = Bcrypt()
    bcrypt.init_app(app)

    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # Fake extension
    challenge_manager = ChallengeManager(app)

    # https://flask.palletsprojects.com/en/3.0.x/templating/#registering-filters
    app.jinja_env.filters["time_ago"] = time_ago

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
