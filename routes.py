from flask import render_template, send_from_directory, request, jsonify, redirect
from constants import *
from flask_login import login_user, logout_user, current_user, login_required
from models import User


def register_routes(app, db, bcrypt, challenge_manager):
    print("Routes registered")

    # ==== Pages ====
    @app.route('/')
    def index():
        return render_template('index.html', user=current_user)

    @app.route('/challenges')
    @login_required
    def challenges():
        unsolved_challenges = challenge_manager.get_unsolved_challenges(current_user)
        return render_template('challenges.html', challenges=unsolved_challenges, user=current_user)

    @app.route('/rules')
    def rules():
        return render_template('rules.html', user=current_user)

    # Setting up the downloads folder
    @app.route('/downloads/<path:filename>', methods=['GET'])
    def download(filename):
        return send_from_directory(DOWNLOAD_FOLDER, filename)

    @app.route('/downloads/')
    def empty_download():
        # Trying to sneakily list all downloads
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

            # Make sure user doesn't exist
            user = User.query.filter(User.username == username).first()
            if user:
                return jsonify(status='error', message='That username is taken.')

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

    # TODO: Leaderboard page
    @app.route('/leaderboard')
    def leaderboard():
        return render_template('leaderboard.html', user=current_user)

    # ==== API ====
    # Flag submission API
    @app.route('/submit-flag', methods=['POST'])
    @login_required
    def submit_flag():
        submitted_flag = request.form['flag'].strip()

        # Look through the challenges to see if the flag matches any of them
        for i, challenge in enumerate(challenge_manager.challenges):
            if submitted_flag == challenge['flag']:
                # Flag was correct
                if current_user.username not in challenge['solvers']:
                    response_message = f"You've earned {challenge['points']} points."
                    current_user.score += challenge['points']
                    db.session.commit()

                    challenge_manager.solve_challenge(i, current_user)

                    return jsonify({'status': 'correct', 'message': response_message})

                # User is trying to resubmit a flag they already submitted
                else:
                    return jsonify({'status': 'already_submitted', 'message': "You've already submitted that flag!"})

        # No hits on any challenges, wrong flag.
        return jsonify({'status': 'wrong', 'message': 'Incorrect flag. Try again!'})

    # TODO: Leaderboard API
    # Returns usernames and scores of all users, sorted
    @app.route('/get-leaderboard', methods=['GET'])
    def get_leaderboard():
        # Query users db
        leaderboard = db.session.query(User.username, User.score).order_by(User.score.desc()).all()

        result = []
        for line in leaderboard:
            result.append({'username': line[0], 'score': line[1]})

        return jsonify(result)

    # ==== Misc ====
    # Favicon
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(STATIC_FOLDER, 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

    # === Robots challenge ===
    @app.route('/robots.txt')
    def robots():
        return send_from_directory(STATIC_FOLDER, 'robots.txt')

    @app.route('/owo_secret.html')
    def owo_secret():
        return send_from_directory(STATIC_FOLDER, 'owo_secret.html')
