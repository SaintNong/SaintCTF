import constants
import datetime


class Solve:
    def __init__(self, username, time):
        self.username = username
        self.time = time

    def __eq__(self, other):
        return self.username == other.username


class ChallengeManager:
    def __init__(self):
        self.challenges = constants.CHALLENGES
        self.recent_solves = []  # List of the most recently solved challenges

        # Replace all newlines in description with the html <br> tags
        for challenge in self.challenges:
            challenge['description'] = challenge['description'].replace('\n', '<br>')

        # Very dirty script to process challenge paths to include the downloads folder
        # 'challenge.txt' => '/downloads/challenge_name/challenge.txt'
        for i, challenge in enumerate(self.challenges):
            if challenge['hosted_onsite']:
                for file_data in challenge['files']:
                    file_data['url'] = f"/downloads/{challenge['folder']}/{file_data['name']}"

    def get_unsolved_challenges(self, user):
        res = []

        for challenge in self.challenges:
            if user.username not in challenge['solvers']:
                res.append(challenge)

        return res

    def solve_challenge(self, index, user):
        solve = Solve(user.username, datetime.datetime.now())
        self.challenges[index]['solvers'].append(user.username)
        self.recent_solves.append(solve)
