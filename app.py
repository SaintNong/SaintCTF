import os
from flask import Flask, request, jsonify, url_for, render_template, send_from_directory
from challenges import ChallengeManager


class CTFPlatform:
    def __init__(self):
        self.app = Flask(__name__)
        self.challenge_manager = ChallengeManager()
        self.data_file = 'users.json'
        self.download_folder = 'downloads'
        self.static_folder = 'static'

        # Initialize routes
        self.initialize_routes()

    def initialize_routes(self):
        """Pages"""

        # Index route
        @self.app.route('/')
        def index():
            return render_template('index.html')

        # Challenges route
        @self.app.route('/challenges')
        def challenges():
            return render_template('challenges.html', challenges=self.challenge_manager.challenges)

        # Rules route
        @self.app.route('/rules')
        def rules():
            return render_template('rules.html')

        # Setting up the downloads folder
        @self.app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
        def download(filename):
            return send_from_directory(self.download_folder, filename)

        # Trying to sneakily list all downloads
        @self.app.route('/downloads/')
        def empty_download():
            return "Nice try"

        """API"""
        # Flag submission API
        @self.app.route('/submit-flag', methods=['POST'])
        def submit_flag():
            submitted_flag = request.form['flag'].strip()

            # Look through the challenges to see if the flag matches any of them
            for challenge in self.challenge_manager.challenges:
                if submitted_flag == challenge['flag']:
                    # Flag was correct
                    response_message = f"You've earned {challenge['points']} points."
                    return jsonify({'success': True, 'message': response_message})

            # No hits on any challenges, wrong flag.
            return jsonify({'success': False, 'message': 'Incorrect flag. Try again!'})

        """Misc"""
        # Favicon
        @self.app.route('/favicon.ico')
        def favicon():
            return send_from_directory(self.static_folder, 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

        # === Robots challenge ===
        @self.app.route('/robots.txt')
        def robots():
            return send_from_directory(self.static_folder, 'robots.txt')

        @self.app.route('/owo_secret.html')
        def owo_secret():
            return send_from_directory(self.static_folder, 'owo_secret.html')

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    platform = CTFPlatform()
    platform.app.run(debug=True)
