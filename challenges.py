import constants
import datetime
from datetime import timedelta
import json


def serialize_datetime(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Not a datetime object")


def deserialize_datetime(json_dict):
    for key, value in json_dict.items():
        try:
            json_dict[key] = datetime.datetime.fromisoformat(value)
        except (ValueError, TypeError):
            continue
    return json_dict


def time_ago(time):
    # Grammatically correct every time, credit to ChatGPT
    now = datetime.datetime.now()
    delta = now - time
    day = delta.days
    hour, remainder = divmod(delta.seconds, 3600)
    minute, second = divmod(remainder, 60)

    if day > 0:
        return f"{day} day{'s' if day > 1 else ''} {hour} hour{'s' if hour > 1 else ''} ago"
    elif hour > 0:
        return f"{hour} hour{'s' if hour > 1 else ''} {minute} minute{'s' if minute > 1 else ''} ago"
    elif minute > 0:
        return f"{minute} minute{'s' if minute > 1 else ''} ago"
    elif second > 5:
        return f"{second} seconds ago"
    else:
        return "Just now"


class ChallengeManager:
    def __init__(self):
        self.challenges = []
        self.recent_solves = []

        self.load_state()

        # Clear solve information and save if RESET_DATA flag is checked
        if constants.RESET_DATA:
            for challenge in self.challenges:
                challenge['solvers'] = []
            self.recent_solves = []
            self.save_state()

        self.initialize_challenges()

    def save_state(self):
        with open(constants.CHALLENGES_FILE_PATH, 'w') as f:
            data = {
                'challenges': self.challenges,
                'recent_solves': self.recent_solves,
            }
            json.dump(data, f, indent=4, default=serialize_datetime)

    def load_state(self):
        with open(constants.CHALLENGES_FILE_PATH, 'r') as f:
            data = json.load(f, object_hook=deserialize_datetime)
            self.challenges = data['challenges']
            self.recent_solves = data['recent_solves']

    def initialize_challenges(self):
        # Replaces
        for challenge in self.challenges:
            challenge['description'] = challenge['description'].replace('\n', '<br>')

            if challenge['has_files']:
                # Calculates challenge files
                for file_data in challenge['files']:
                    if file_data.get('url') is None:
                        file_data['url'] = f"/downloads/{challenge['folder']}/{file_data['name']}"

    def solve_challenge(self, index, user):
        solve = {
            'username': user.username,
            'time': datetime.datetime.now(),
            'challenge_id': index,
        }

        self.challenges[index]['solvers'].append(user.username)
        self.recent_solves.insert(0, solve)
        self.save_state()

    # Gets the all challenges the user has solved, and how long ago they solved it
    def get_solved_challenges(self, username):
        return [{
            "time": solve['time'],
            "challenge": self.challenges[solve['challenge_id']],
            "time_ago": time_ago(solve['time'])
        } for solve in self.recent_solves if solve['username'] == username]

    # Returns the last n recent solves
    def get_recent_solves(self, n):
        recent_solves = []
        for solve in self.recent_solves:
            challenge = self.challenges[solve['challenge_id']]
            recent_solves.append({
                "solver": solve['username'],
                "challenge": challenge,
                "time": solve['time'],
                "time_ago": time_ago(solve['time'])
            })

            if len(recent_solves) == n:
                break

        return recent_solves

    def get_time_based_leaderboard(self, top_users):
        dataset = []

        top_cumulative_scores = {}
        for user in top_users:
            top_cumulative_scores[user] = 0

        # Go from the oldest solve to the latest one
        for solve in self.recent_solves[::-1]:
            if solve['username'] in top_users:
                username = solve['username']
                solved_challenge = self.challenges[solve['challenge_id']]
                weight = solved_challenge['points']

                # The instant before this solve, they were at the score they were at before
                dataset.append({
                    "time": (solve['time'] - timedelta(milliseconds=1)).isoformat(),
                    "user": solve['username'],
                    "points": top_cumulative_scores[username],
                })

                # The instant when they solve the challenge, they jump up to however many points the
                # challenge was worth
                top_cumulative_scores[username] += weight
                dataset.append({
                    "time": solve['time'].isoformat(),
                    "user": solve['username'],
                    "points": top_cumulative_scores[username],
                })

        # At the present time, all the users have the score they currently have, so we add that too
        for user in top_cumulative_scores.keys():
            dataset.append({
                "time": datetime.datetime.now().isoformat(),
                "user": user,
                "points": top_cumulative_scores[user],
            })

        return dataset
