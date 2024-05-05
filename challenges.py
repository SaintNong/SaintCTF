import datetime
from datetime import timedelta
import os
import tomllib

from constants import CHALLENGES_DIRECTORY, DIFFICULTY_MAPPING
from models import Solve, User, db


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
        self.challenges = {}
        self.read_challenges()

    def read_challenges(self):
        for challenge_id in os.listdir(CHALLENGES_DIRECTORY):
            # Get the directory of the challenge
            downloads_dir = os.path.join(CHALLENGES_DIRECTORY, challenge_id, "downloads")

            # Read the challenge configuration file
            toml_file = os.path.join(CHALLENGES_DIRECTORY, challenge_id, "challenge.toml")
            if os.path.isfile(toml_file):
                with open(toml_file, "rb") as file:
                    challenge_data = tomllib.load(file)

                    # Fix newlines
                    challenge_data['description'] = challenge_data['description'].replace('\n', '<br>')
            else:
                raise FileNotFoundError(f"Could not find challenge.toml file for challenge '{challenge_id}'")

            # Begin adding challenge files
            challenge_data['files'] = []

            for entry in os.scandir(downloads_dir):
                # Skip non-files (i.e. folders)
                if not entry.is_file():
                    continue

                # Add file download metadata
                challenge_data['files'].append(entry.name)

            # Add the challenge
            self.challenges[challenge_id] = challenge_data

        try:
            # Sort challenges by difficulty
            self.challenges = dict(
                sorted(self.challenges.items(), key=lambda x: DIFFICULTY_MAPPING[x[1]['difficulty']]))
        except KeyError:
            # Oh no, someone made a new difficulty
            raise KeyError("It seems someone tried to make a new difficulty...")

    @staticmethod
    def solve_challenge(id_, user):
        solve = Solve(user_id=user.id, challenge_id=id_)
        db.session.add(solve)
        db.session.commit()

    # Gets the all challenges the user has solved, and how long ago they solved it
    def get_user_solved_challenges(self, user_id):
        solves = Solve.query.filter_by(user_id=user_id).order_by(Solve.time.desc()).all()
        return [{
            "time": solve.time,
            "challenge": self.challenges[solve.challenge_id],
            "time_ago": time_ago(solve.time)
        } for solve in solves]

    # Returns the last n recent solves
    def get_recent_solves(self, n):
        recent_solves = Solve.query.order_by(Solve.time.desc()).limit(n)
        return [{
            "solver": solve.user.username,
            "challenge": self.challenges[solve.challenge_id],
            "time": solve.time,
            "time_ago": time_ago(solve.time)
        } for solve in recent_solves]

    def get_leaderboard_graph_data(self, top_user_ids):
        dataset = []
        top_cumulative_scores = {user_id: 0 for user_id in top_user_ids}

        # Fetch solves from the database for the given top users, ordered by time ascending
        solves = Solve.query.filter(Solve.user_id.in_(top_user_ids)).order_by(Solve.time.asc()).all()

        for solve in solves:
            user_id = solve.user_id
            challenge = self.challenges[solve.challenge_id]
            points = challenge['points']

            # The instant before this solve, they were at the score they were at before
            dataset.append({
                "time": (solve.time - timedelta(milliseconds=1)).isoformat(),
                "user": solve.user.username,
                "points": top_cumulative_scores[user_id]
            })

            # The instant when they solve the challenge, they jump up to however many points the challenge was worth
            top_cumulative_scores[user_id] += points
            dataset.append({
                "time": solve.time.isoformat(),
                "user": solve.user.username,
                "points": top_cumulative_scores[user_id]
            })

        # At the current time, all users have their current points
        now = datetime.datetime.now().isoformat()
        for user_id in top_cumulative_scores:
            user = User.query.get(user_id)

            # Add current score
            dataset.append({
                "time": now,
                "user": user.username if user else "Unknown",
                "points": top_cumulative_scores[user_id]
            })

        return dataset
