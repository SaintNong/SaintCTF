import flask_login
from flask import (
    render_template,
    send_from_directory,
    request,
    jsonify,
    redirect,
    abort,
    url_for,
    Response,
)
from constants import *
from flask_login import login_user, logout_user, current_user, login_required
from models import User, Solve
from challenges import ChallengeManager
from datetime import timedelta
import itertools
import re

from sqlalchemy import event, select
import json

from sse import SSEQueue

sse_queue = SSEQueue()
first_blood = []


def register_routes(app, db, bcrypt, challenge_manager: ChallengeManager, csrf):
    app.logger.info("Routes registered")

    @event.listens_for(Solve, "after_insert")
    def solveTableChanged(_mapper, connection, _target):
        # Get 'first blood' solves
        solves = db.session.scalars(db.select(Solve).order_by(Solve.time.asc())).all()

        global first_blood
        first_blood = []
        first_solved = []
        for solve in solves:
            if solve.challenge_id not in first_solved:
                first_solved.append(solve.challenge_id)
                first_blood.append(solve.id)

        # Get last 12 recent solves
        recent_solves = challenge_manager.get_recent_solves(12, first_blood)
        sse_queue.put(("recentActivity", json.dumps(recent_solves)))

        top_players = challenge_manager.get_top_players()
        sse_queue.put(("leaderboard", json.dumps(top_players)))

        # Update leaderboard chart
        # NOTE: This relies on *both* the user table and solve table, and ideally,
        #       the event would be dispatched when either one changes - however,
        #       the leaderboard chart currently only sorts with the score in the
        #       user table; all other scoring information used in the chart comes
        #       from the solve table.
        # Get top 10 players
        top_players = top_players[:10]
        top_ids = []
        for player in top_players:
            top_ids.append(player["id"])

        # Get datapoints
        data_points = challenge_manager.get_leaderboard_chart_data(top_ids)
        sse_queue.put(("chart", json.dumps(data_points)))

    # ==== Pages ====
    @app.route("/")
    def index():
        statistics = {
            "challenges": len(challenge_manager.challenges),
            "solves": db.session.scalar(db.select(db.func.count(Solve.id))),
            "points": {
                "accrued": challenge_manager.get_total_points(
                    db.session.scalars(
                        db.select(Solve).options(db.load_only(Solve.challenge_id))
                    )
                ),
                "available": sum(
                    map(lambda x: x["points"], challenge_manager.challenges.values())
                ),
            },
            "players": db.session.scalar(db.select(db.func.count(User.id))),
        }
        return render_template("index.html", user=current_user, stats=statistics)

    @app.route("/challenges")
    @login_required
    def challenges():
        # Generate the url for any challenge containers
        # NOTE: This cannot be done in ChallengeManager because it requires app context
        #       i.e. it requires you to be in a request
        for id_, challenge in challenge_manager.challenges.items():
            container = challenge["container"]
            if container:
                # Calculate new url from current url and port
                current_url = url_for(request.endpoint, _external=True)
                parts = current_url.split(":")
                container_url = f"{parts[0]}:{parts[1]}:{container['port']}"

                # Set container URL in the challenge data
                container["url"] = container_url

        # Select all solves, ordered by challenge_id (needed for `groupby`)
        solves = db.session.scalars(
            db.select(Solve).order_by(Solve.challenge_id, Solve.time.asc())
        ).all()

        # Remove solves that do not correspond to known challenges
        # (in case challenges have been removed)
        solves = [x for x in solves if x.challenge_id in challenge_manager.challenges]

        # Save list of user's solved challenges
        user_solves = [x for x in solves if x.user == current_user]

        # Calculate score
        score = challenge_manager.get_total_points(user_solves)

        # Save count of user's solved challenges
        solved_count = len(user_solves)

        # Group solves by challenge_id
        # https://stackoverflow.com/a/51416299
        solves = {
            k: list(g)
            for k, g in itertools.groupby(solves, key=lambda x: x.challenge_id)
        }

        return render_template(
            "challenges.html",
            challenges=challenge_manager.challenges,
            solves=solves,
            solved_count=solved_count,
            user=current_user,
            score=score,
        )

    # Setting up challenge downloads
    @app.route("/downloads/<challenge_id>/<path:filepath>", methods=["GET"])
    def download(challenge_id, filepath):
        challenge = challenge_manager.challenges.get(challenge_id)

        if challenge is None:  # Challenge ID not found
            abort(404)  # https://stackoverflow.com/a/69234618

        if filepath in challenge["files"]:
            return send_from_directory(
                CHALLENGES_DIRECTORY, challenge_id + "/downloads/" + filepath
            )
        else:
            abort(404)

    @app.route("/rules")
    def rules():
        return render_template("rules.html", user=current_user)

    @app.route("/downloads/")
    def empty_download():
        # Trying to sneakily list all challenges
        return "Nice try"

    # Logout endpoint
    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        return redirect("/")

    # Delete account endpoint
    @app.route("/delete_account", methods=["POST"])
    @login_required
    def delete_account():
        name = User.query.filter(User.id == current_user.id).first().username
        app.logger.debug(f"Deleted account {name}")
        Solve.query.filter(Solve.user_id == current_user.id).delete()
        User.query.filter(User.id == current_user.id).delete()

        db.session.commit()

        return redirect("/")

    # Signup page
    @app.route("/register", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                return jsonify({"error": "Missing username or password"})

            # Make sure user doesn't exist
            user = User.query.filter(User.username == username).first()
            if user:
                return jsonify(status="error", message="That username is taken.")

            # Make sure the username is in allowed characters list
            if not re.match("^[A-Za-z0-9_]+$", username):
                return jsonify(
                    status="error",
                    message="Username can only contain letters, numbers, and underscores.",
                )

            # Make sure the username and password are the right length
            if len(password) < 8 or len(password) > 40:
                return jsonify(
                    status="error",
                    message="Password must be between 8 and 40 characters long.",
                )
            elif len(username) < 1 or len(username) > 20:
                return jsonify(
                    status="error",
                    message="Username must be between 1 and 20 characters long.",
                )

            # Hash password before storing
            hashed_password = bcrypt.generate_password_hash(password)
            user = User()
            user.username = username
            user.password = hashed_password
            user.score = 0

            # Add user to database
            db.session.add(user)
            db.session.commit()

            # Login the user into the account they created
            login_user(user)

            return jsonify(status="success", message="User created")

        else:
            return render_template("register.html", user=current_user)

    # Login page
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # Look for specified user
            user = User.query.filter(User.username == username).first()
            if user is None:
                return jsonify(
                    status="error",
                    message="Either the username or password is incorrect",
                )

            # Check if hashes match
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return jsonify(status="success", message="Logged in successfully")
            else:
                return jsonify(
                    status="error",
                    message="Either the username or password is incorrect",
                )
        else:
            return render_template("login.html", user=current_user)

    @app.route("/leaderboard")
    def leaderboard():
        return render_template("leaderboard.html", user=current_user)

    @app.route("/solves")
    def solves():
        solves = db.session.scalars(db.select(Solve).order_by(Solve.time.asc())).all()

        return render_template(
            "solves.html",
            user=current_user,
            solves=solves,
            first_blood=first_blood,
            challenges=challenge_manager.challenges,
        )

    # Shows the profile of specific user with uid
    @app.route("/profile/<int:user_id>")
    def profile(user_id):
        # Query database for user
        displayed_user = db.session.query(User).filter(User.id == user_id).first()

        # Ensure user exists
        if displayed_user is None:
            abort(404, "This player does not exist.")

        solves = Solve.query.filter_by(user_id=user_id).order_by(Solve.time.asc()).all()
        score = challenge_manager.get_total_points(solves)

        # For solve table
        solves = challenge_manager.get_user_solved_challenges(solves, first_blood)

        # For graph
        user_graph_datapoints = challenge_manager.get_user_profile_graph(
            displayed_user.id
        )

        # Calculate user rank
        top_players = challenge_manager.get_top_players()
        rank = 1
        for player in top_players:
            if player["id"] == user_id:
                break
            rank += 1

        return render_template(
            "profile.html",
            user=current_user,
            score=score,
            displayed_user=displayed_user,
            graph_datapoints=user_graph_datapoints,
            solves=solves,
            timedelta=timedelta,
            rank=rank,
        )

    # ==== API ====
    # Flag submission API
    @app.route("/submit-flag", methods=["POST"])
    @login_required
    def submit_flag():
        submitted_flag = request.form["flag"].strip()

        # Look through the challenges to see if the flag matches any of them
        for id_, challenge in challenge_manager.challenges.items():
            # Flag was correct
            if submitted_flag == challenge["flag"]:

                # Check if the user already solved the challenge
                solve = Solve.query.filter_by(
                    user_id=current_user.id, challenge_id=id_
                ).first()
                if solve is None:
                    response_message = f"You've earned {challenge['points']} points for <code>{challenge['name']}</code>."

                    challenge_manager.solve_challenge(id_, current_user)

                    return jsonify({"status": "correct", "message": response_message})

                # User is trying to resubmit a flag they already submitted
                else:
                    return jsonify(
                        {
                            "status": "already_submitted",
                            "message": f"You've already submitted that flag for <code>{challenge['name']}</code>!",
                        }
                    )

        # No hits on any challenges, wrong flag.
        return jsonify({"status": "wrong", "message": "Incorrect flag. Try again!"})

    @app.route("/leaderboard-events", methods=["GET"])
    def get_leaderboard_events():
        def eventStream():
            q = sse_queue.listen()

            # Send data when event stream is initially connected to
            with app.app_context():
                with db.engine.connect() as connection:
                    solveTableChanged(None, connection, None)

            while True:
                event_type, data = q.get()
                yield f"event: {event_type}\ndata: {data}\n\n"

        return Response(eventStream(), mimetype="text/event-stream")

    # ==== Misc ====
    # Favicon
    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            STATIC_DIRECTORY, "images/favicon.ico", mimetype="image/vnd.microsoft.icon"
        )

    # Robots
    @app.route("/robots.txt")
    def robots():
        return send_from_directory(STATIC_DIRECTORY, "robots.txt")
