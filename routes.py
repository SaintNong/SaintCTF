from flask import render_template, send_from_directory, request, jsonify, redirect, abort
from constants import *
from flask_login import login_user, logout_user, current_user, login_required
from models import User, Solve
from challenges import ChallengeManager
from datetime import timedelta
import itertools
import re


def register_routes(app, db, bcrypt, challenge_manager: ChallengeManager):
    print("Routes registered")

    # ==== Pages ====
    @app.route('/')
    def index():
        return render_template('index.html', user=current_user)

    @app.route('/challenges')
    @login_required
    def challenges():
        # Select all solves, ordered by challenge_id (needed for `groupby`)
        solves = db.session.scalars(db.select(Solve).order_by(Solve.challenge_id, Solve.time.asc())).all()

        # Remove solves that do not correspond to known challenges
        # (in case challenges have been removed)
        solves = [x for x in solves if x.challenge_id in challenge_manager.challenges]

        # Save count of user's solved challenges
        solved_count = len([x for x in solves if x.user == current_user])

        # Group solves by challenge_id
        # https://stackoverflow.com/a/51416299
        solves = {k: list(g) for k, g in itertools.groupby(solves, key=lambda x: x.challenge_id)}

        return render_template('challenges.html', challenges=challenge_manager.challenges, solves=solves, solved_count=solved_count, user=current_user)

    # Setting up challenge downloads
    @app.route('/downloads/<challenge>/<path:filepath>', methods=['GET'])
    def download(challenge, filepath):
        challenge = challenge_manager.challenges.get(challenge)

        if challenge is None: # Challenge ID not found
            abort(404) # https://stackoverflow.com/a/69234618

        if filepath in challenge['files']:
            return send_from_directory(CHALLENGES_DIRECTORY, challenge + "/" + filepath)
        else:
            abort(404)

    @app.route('/rules')
    def rules():
        return render_template('rules.html', user=current_user)

    @app.route('/downloads/')
    def empty_download():
        # Trying to sneakily list all challenges
        return "Nice try"

    # Logout page
    @app.route('/logout', methods=['GET', 'POST'])
    def logout():
        logout_user()
        return redirect('/')

    # Signup page
    @app.route('/register', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                return jsonify({'error': 'Missing username or password'})

            # Make sure user doesn't exist
            user = User.query.filter(User.username == username).first()
            if user:
                return jsonify(status='error', message='That username is taken.')

            # Make sure the username is in allowed characters list
            if not re.match('^[A-Za-z0-9_]+$', username):
                return jsonify(status='error', message='Username can only contain letters, numbers, and underscores.')

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

            return jsonify(status='success', message='User created')

        else:
            return render_template('register.html', user=current_user)

    # Login page
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            # Look for specified user
            user = User.query.filter(User.username == username).first()
            if user is None:
                return jsonify(status='error', message='Either the username or password is incorrect')

            # Check if hashes match
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return jsonify(status='success', message='Logged in successfully')
            else:
                return jsonify(status='error', message='Either the username or password is incorrect')
        else:
            return render_template('login.html', user=current_user, login_msg=False)

    @app.route('/leaderboard')
    def leaderboard():
        return render_template('leaderboard.html', user=current_user)

    # Shows the profile of specific user with uid
    @app.route('/profile/<int:user_id>')
    @login_required
    def profile(user_id):
        # Query database for user
        displayed_user = db.session.query(User).filter(User.id == user_id).first()

        if displayed_user is None:
            abort(404, "This player does not exist.")

        solves = challenge_manager.get_user_solved_challenges(displayed_user.id)

        # Calculate user rank
        top_players = db.session.query(User.username, User.score, User.id).order_by(User.score.desc()).all()
        rank = 1
        for player in top_players:
            if player.id == user_id:
                break
            rank += 1

        return render_template('profile.html', user=current_user, displayed_user=displayed_user,
                               solves=solves, timedelta=timedelta, rank=rank)

    # ==== API ====
    # Flag submission API
    @app.route('/submit-flag', methods=['POST'])
    @login_required
    def submit_flag():
        submitted_flag = request.form['flag'].strip()

        # Look through the challenges to see if the flag matches any of them
        for id_, challenge in challenge_manager.challenges.items():
            # Flag was correct
            if submitted_flag == challenge['flag']:

                # Check if the user already solved the challenge
                solve = Solve.query.filter_by(user_id=current_user.id, challenge_id=id_).first()
                if solve is None:
                    response_message = f"You've earned {challenge['points']} points."
                    current_user.score += challenge['points']
                    db.session.commit()

                    challenge_manager.solve_challenge(id_, current_user)

                    return jsonify({'status': 'correct', 'message': response_message})

                # User is trying to resubmit a flag they already submitted
                else:
                    return jsonify({'status': 'already_submitted', 'message': "You've already submitted that flag!"})

        # No hits on any challenges, wrong flag.
        return jsonify({'status': 'wrong', 'message': 'Incorrect flag. Try again!'})

    @app.route('/get-leaderboard', methods=['GET'])
    def get_leaderboard():
        # Query users db
        top_players = db.session.query(User.username, User.score, User.id).order_by(User.score.desc()).all()

        result = []
        for line in top_players:
            result.append({'username': line[0], 'score': line[1], 'user_id': line[2]})

        return jsonify(result)

    @app.route('/get-recent-solves', methods=['GET'])
    def get_recent_solves():
        # Get last 12 recent solves
        recent_solves = challenge_manager.get_recent_solves(12)

        return jsonify(recent_solves)

    @app.route('/get-leaderboard-graph-data', methods=['GET'])
    def get_leaderboard_graph():
        # Get top 10 players
        top_players = db.session.query(User.id, User.score).order_by(User.score.desc()).limit(10).all()
        top_ids = []
        for player in top_players:
            top_ids.append(player.id)

        # Get datapoints
        data_points = challenge_manager.get_leaderboard_graph_data(top_ids)

        return data_points

    # ==== Misc ====
    # Favicon
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(STATIC_DIRECTORY, 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

    # === Robots challenge ===
    @app.route('/robots.txt')
    def robots():
        return send_from_directory(STATIC_DIRECTORY, 'robots.txt')

    @app.route('/owo_secret.html')
    def owo_secret():
        return send_from_directory(STATIC_DIRECTORY, 'owo_secret.html')
