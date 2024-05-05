import datetime
from datetime import timedelta
import os
import tomllib
import docker
import signal

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


class ContainerManager:
    """It manages containers"""

    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}
        print("Container manager initialized")

        # Stop containers when program is closed
        signal.signal(signal.SIGINT, self.clean_up_containers)
        signal.signal(signal.SIGTERM, self.clean_up_containers)

    def add_container(self, container_data, container_dir, challenge_id):
        client = self.client

        # Try creating the container
        try:
            # Build container
            self.client.images.build(tag=challenge_id, path=container_dir)

            # Run container with our port bound
            print(f" * Starting container '{challenge_id}'")
            port = {container_data['port']: container_data['port']}
            container = client.containers.run(challenge_id, auto_remove=True, detach=True, ports=port, labels=['CTF'])

            # Add container
            self.containers[challenge_id] = container

        # Error handling
        except docker.errors.ImageNotFound:
            print(f" * Dockerfile for {challenge_id} is missing")
        except docker.errors.APIError as e:
            print(f" * Docker API encountered an error while starting {challenge_id}")
            raise e

    def clean_up_containers(self, signum, frame):
        # Stops all containers - called on program exit
        print("Stopping containers")

        for challenge_id, container in self.containers.items():
            container.kill()
            print(f" * Killed container '{challenge_id}'")


class ChallengeManager:
    def __init__(self):
        self.challenges = {}
        self.container_manager = ContainerManager()

        self.read_challenges()

    def read_challenges(self):
        for challenge_id in os.listdir(CHALLENGES_DIRECTORY):
            challenge_toml = os.path.join(CHALLENGES_DIRECTORY, challenge_id, 'challenge.toml')
            downloads_dir = os.path.join(CHALLENGES_DIRECTORY, challenge_id, 'downloads')

            container_toml = os.path.join(CHALLENGES_DIRECTORY, challenge_id, 'container.toml')
            container_dir = os.path.join(CHALLENGES_DIRECTORY, challenge_id, 'container')

            # Read the challenge configuration file
            if os.path.isfile(challenge_toml):
                with open(challenge_toml, 'rb') as file:
                    challenge_data = tomllib.load(file)

                    # Fix newlines
                    challenge_data['description'] = challenge_data['description'].replace('\n', '<br>')
            else:
                raise FileNotFoundError(f"Could not find challenge.toml file for challenge '{challenge_id}'")

            # Add challenge downloadable files if applicable
            challenge_data['files'] = []
            if os.path.exists(downloads_dir):
                for entry in os.scandir(downloads_dir):
                    # Skip non-files (i.e. folders)
                    if not entry.is_file():
                        continue

                    # Add file download metadata
                    challenge_data['files'].append(entry.name)

            # Add the challenge
            self.challenges[challenge_id] = challenge_data

            # Start the challenge's Docker container, if needed
            self.challenges[challenge_id]['container'] = {}
            if os.path.exists(container_toml):
                # Read container metadata
                with open(container_toml, "rb") as file:
                    container_data = tomllib.load(file)
                    self.challenges[challenge_id]['container'] = container_data

                if os.path.exists(container_dir):

                    self.container_manager.add_container(container_data, container_dir, challenge_id)
                else:
                    raise FileNotFoundError(
                        f"No container folder found for '{challenge_id}', but container.toml was defined")

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
