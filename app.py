import os

from flask import Flask, request, jsonify, url_for, render_template, send_from_directory
from challenges import ChallengeManager

app = Flask(__name__)
challenge_manager = ChallengeManager()

DATA_FILE = 'users.json'
DOWNLOAD_FOLDER = 'downloads'
STATIC_FOLDER = 'static'


@app.route('/downloads/')
def empty_download():
    return "Nice try, not gonna work tho"


# Setup downloads folder
@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)


@app.route('/submit-flag', methods=['POST'])
def submit_flag():
    submitted_flag = request.form['flag'].strip()
    for challenge in challenge_manager.challenges:
        if submitted_flag == challenge['flag']:
            response_message = f"You've earned {challenge['points']} points."
            return jsonify({'success': True, 'message': response_message})

    return jsonify({'success': False, 'message': 'Incorrect flag. Try again!'}), 400


@app.route('/challenges')
def challenges():
    return render_template('challenges.html', challenges=challenge_manager.challenges)


@app.route('/rules')
def rules():
    return render_template('rules.html')


# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(STATIC_FOLDER, 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')


# Robots challenge
@app.route('/robots.txt')
def robots():
    return send_from_directory(STATIC_FOLDER, 'robots.txt')


@app.route('/owo_secret.html')
def owo_secret():
    return send_from_directory(STATIC_FOLDER, 'owo_secret.html')


@app.route('/')
def index():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)
