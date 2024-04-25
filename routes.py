from flask import render_template, send_from_directory, request, jsonify
from constants import *


def register_routes(app, db, bcrypt, challenge_manager):
    print("Routes registered")

    # ==== Pages ====
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/challenges')
    def challenges():
        return render_template('challenges.html', challenges=challenge_manager.challenges)

    @app.route('/rules')
    def rules():
        return render_template('rules.html')

    # Setting up the downloads folder
    @app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
    def download(filename):
        return send_from_directory(DOWNLOAD_FOLDER, filename)

    @app.route('/downloads/')
    def empty_download():
        # Trying to sneakily list all downloads
        return "Nice try"

    # Login page
    @app.route('/login')
    def login():
        return render_template('login.html')

    # Registration page
    @app.route('/register')
    def register():
        return render_template('register.html')

    # ==== API ====
    # Flag submission API
    @app.route('/submit-flag', methods=['POST'])
    def submit_flag():
        submitted_flag = request.form['flag'].strip()

        # Look through the challenges to see if the flag matches any of them
        for challenge in challenge_manager.challenges:
            if submitted_flag == challenge['flag']:
                # Flag was correct
                response_message = f"You've earned {challenge['points']} points."
                return jsonify({'success': True, 'message': response_message})

        # No hits on any challenges, wrong flag.
        return jsonify({'success': False, 'message': 'Incorrect flag. Try again!'})

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
