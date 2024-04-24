from flask import Flask, request, jsonify, make_response, render_template, send_from_directory
from challenges import ChallengeManager

app = Flask(__name__)
challenge_manager = ChallengeManager()

DATA_FILE = 'users.json'
DOWNLOAD_FOLDER = 'downloads'


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


@app.route('/')
def challenges():
    return render_template('challenges.html', challenges=challenge_manager.challenges)


if __name__ == '__main__':
    app.run(debug=True)
