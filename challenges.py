import datetime
from datetime import timedelta
import os
import tomllib
import signal
import sys
from models import Solve, User, db

from constants import CHALLENGES_DIRECTORY, DIFFICULTY_MAPPING, HAS_DOCKER

if HAS_DOCKER:
    import docker


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

    def __init__(self, app):
        self.client = docker.from_env()
        self.app = app
        print("Container manager initialised")

        # Stop containers when program is closed
        signal.signal(signal.SIGINT, self.exit_flask)
        signal.signal(signal.SIGTERM, self.exit_flask)

    # The sole reason that this exists is sometimes we want to kill containers without quitting,
    # and signal.signal() requires a function with no arguments
    def exit_flask(self, signal, frame):
        self.clean_up_containers()
        sys.exit()

    def run_container(self, container_data, container_dir, challenge_id):
        client = self.client

        # Try creating the container
        try:
            # Build container
            self.client.images.build(tag=challenge_id, path=container_dir)

        except docker.errors.APIError as e:
            print(f" * Docker API encountered an error while building")
            raise e

        try:
            # Check if the container we need is already running, if not, start it
            containers = self.client.containers.list(
                filters={"label": ["CTF", challenge_id]}
            )

            if not containers:
                port = {container_data["port"]: container_data["port"]}
                container = client.containers.run(
                    challenge_id,
                    auto_remove=True,
                    detach=True,
                    ports=port,
                    labels=["CTF", challenge_id],
                )
                print(
                    f' * Started container for challenge "{challenge_id}" with ID of "{container.name}"'
                )
            else:
                for container in containers:
                    print(
                        f' * Container already running for "{challenge_id}" with ID of "{container.name}"'
                    )

        # Error handling
        except docker.errors.ImageNotFound:
            print(f" * Dockerfile for {challenge_id} is missing")
        except docker.errors.APIError as e:
            print(f" * Docker API encountered an error while starting {challenge_id}")
            raise e

    def clean_up_containers(self):
        # Stops all containers - called on program exit and when starting
        print(" * Stopping containers")
        # List all containers started by the CTF, and kill them
        for container in self.client.containers.list(filters={"label": ["CTF"]}):
            try:
                labels = list(container.labels.keys())
                container.stop()
                print(
                    f' * Stopped container for "{labels[1]}" of ID "{container.name}" '
                )
            except docker.errors.APIError as e:
                # Due to Flask's debug mode, this method may be called twice
                # where the second invocation fails to find the container, as
                # it is already stopped - thus we exclude this error
                if e.status_code != 404:
                    print(f" * Docker API encountered an error while cleaning")
                    raise e


class ChallengeManager:
    def __init__(self, app):
        self.challenges = {}

        if HAS_DOCKER:
            self.container_manager = ContainerManager(app)
        else:
            self.container_manager = None

        self.read_challenges()

    def read_challenges(self):
        print(" * Reading challenges and containers")
        for challenge_id in os.listdir(CHALLENGES_DIRECTORY):
            challenge_directory = os.path.join(CHALLENGES_DIRECTORY, challenge_id)

            # Get paths for challenge files and folders
            challenge_toml = os.path.join(challenge_directory, "challenge.toml")
            downloads_dir = os.path.join(challenge_directory, "downloads")
            container_toml = os.path.join(challenge_directory, "container.toml")
            container_dir = os.path.join(challenge_directory, "container")

            # Read the challenge configuration file
            challenge_data = self.read_toml_file(challenge_toml, challenge_id)
            challenge_data["description"] = (
                challenge_data["description"].strip().replace("\n", "<br>")
            )  # Fix newlines

            # Add challenge downloadable files if applicable
            challenge_data["files"] = []
            if os.path.exists(downloads_dir):
                print(f' * Creating downloads for challenge "{challenge_id}"')
                for entry in os.scandir(downloads_dir):
                    # Skip non-files (i.e. folders)
                    if not entry.is_file():
                        continue

                    # Add file download metadata
                    challenge_data["files"].append(entry.name)

            # Start the challenge's Docker container, if needed
            challenge_data["container"] = {}
            if os.path.exists(container_toml):
                # Skip challenges that require containers if the Docker API is not present
                if not HAS_DOCKER:
                    print(
                        f"Warning: skipped challenge '{challenge_id}' requiring containerisation"
                    )
                    continue

                # Read container metadata
                container_data = self.read_toml_file(container_toml, challenge_id)
                challenge_data["container"] = container_data

                if os.path.exists(container_dir):
                    self.container_manager.run_container(
                        container_data, container_dir, challenge_id
                    )
                else:
                    raise FileNotFoundError(
                        f"No container folder found for '{challenge_id}', but container.toml was defined"
                    )

            # Add the challenge data
            self.challenges[challenge_id] = challenge_data

        try:
            # Sort challenges by difficulty
            self.challenges = dict(
                sorted(
                    self.challenges.items(),
                    key=lambda x: DIFFICULTY_MAPPING[x[1]["difficulty"]],
                )
            )
        except KeyError:
            # Oh no, someone made a new difficulty
            raise KeyError("It seems someone tried to make a new difficulty...")

    @staticmethod
    def read_toml_file(file_path, challenge_id):
        if not os.path.exists(file_path):
            filename = os.path.basename(file_path)
            raise FileNotFoundError(
                f"Could not find '{filename}' for challenge '{challenge_id}'"
            )

        with open(file_path, "rb") as file:
            return tomllib.load(file)

    @staticmethod
    def solve_challenge(id_, user):
        solve = Solve(user_id=user.id, challenge_id=id_)
        db.session.add(solve)
        db.session.commit()

    # Gets the all challenges the user has solved, and how long ago they solved it
    def get_user_solved_challenges(self, user_id):
        solves = (
            Solve.query.filter_by(user_id=user_id).order_by(Solve.time.desc()).all()
        )
        return [
            {
                "time": solve.time,
                "challenge": self.challenges[solve.challenge_id],
                "time_ago": time_ago(solve.time),
            }
            for solve in solves
        ]

    # Returns the last n recent solves
    def get_recent_solves(self, n):
        recent_solves = Solve.query.order_by(Solve.time.desc()).limit(n)
        return [
            {
                "solver": solve.user.username,
                "challenge": self.challenges[solve.challenge_id],
                "time": solve.time,
                "time_ago": time_ago(solve.time),
            }
            for solve in recent_solves
        ]

    def get_leaderboard_graph_data(self, top_user_ids):
        dataset = []
        top_cumulative_scores = {user_id: 0 for user_id in top_user_ids}

        # Fetch solves from the database for the given top users, ordered by time ascending
        solves = (
            Solve.query.filter(Solve.user_id.in_(top_user_ids))
            .order_by(Solve.time.asc())
            .all()
        )

        for solve in solves:
            user_id = solve.user_id
            challenge = self.challenges[solve.challenge_id]
            points = challenge["points"]

            # The instant before this solve, they were at the score they were at before
            dataset.append(
                {
                    "time": (solve.time - timedelta(milliseconds=1)).isoformat(),
                    "user": solve.user.username,
                    "points": top_cumulative_scores[user_id],
                }
            )

            # The instant when they solve the challenge, they jump up to however many points the challenge was worth
            top_cumulative_scores[user_id] += points
            dataset.append(
                {
                    "time": solve.time.isoformat(),
                    "user": solve.user.username,
                    "points": top_cumulative_scores[user_id],
                }
            )

        # At the current time, all users have their current points
        now = datetime.datetime.now().isoformat()
        for user_id in top_cumulative_scores:
            user = User.query.get(user_id)

            # Add current score
            dataset.append(
                {
                    "time": now,
                    "user": user.username if user else "Unknown",
                    "points": top_cumulative_scores[user_id],
                }
            )

        return dataset
