from collections import defaultdict
import datetime
import jinja2
import os
import tomlkit
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


# A Jinja filter that converts a regular challenge ID into a URL-encoded ID for anchor links
@jinja2.pass_environment
def challenge_anchor_id(env, id_):
    return "chall-" + env.filters["urlencode"](id_)


class ContainerManager:
    """It manages containers"""

    def __init__(self, app):
        self.client = docker.from_env()
        self.app = app
        self.app.logger.info("Container manager initialised")

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
            self.app.logger.info(f"Docker API encountered an error while building")
            raise e

        try:
            # Check if the container we need is already running, if not, start it
            containers = self.client.containers.list(
                filters={"label": ["CTF", challenge_id]}
            )

            if not containers:
                port = {container_data["port"]: container_data["port"]}
                self.app.logger.info(f"{challenge_id}: Starting container")
                container = client.containers.run(
                    challenge_id,
                    auto_remove=True,
                    detach=True,
                    ports=port,
                    labels=["CTF", challenge_id],
                )
                self.app.logger.info(
                    f"{challenge_id}: Started container '{container.name}'"
                )
            else:
                for container in containers:
                    self.app.logger.info(
                        f"{challenge_id}: Container already running ({container.name})"
                    )

        # Error handling
        except docker.errors.ImageNotFound:
            self.app.logger.info(f"{challenge_id}: Dockerfile is missing")
        except docker.errors.APIError as e:
            self.app.logger.info(
                f"{challenge_id}: Docker API encountered an error while starting"
            )
            raise e

    def clean_up_containers(self):
        # Stops all containers - called on program exit and when starting
        self.app.logger.info("Stopping containers")
        # List all containers started by the CTF, and kill them
        for container in self.client.containers.list(filters={"label": ["CTF"]}):
            try:
                labels = list(container.labels.keys())
                container.stop()
                self.app.logger.info(
                    f"{labels[1]}: Stopped container ({container.name})"
                )
            except docker.errors.APIError as e:
                # Due to Flask's debug mode, this method may be called twice
                # where the second invocation fails to find the container, as
                # it is already stopped - thus we exclude this error
                if e.status_code != 404:
                    self.app.logger.info(
                        f"Docker API encountered an error while cleaning"
                    )
                    raise e


class ChallengeManager:
    def __init__(self, app):
        self.challenges = {}
        self.app = app

        if HAS_DOCKER and self.app.config["FORCE_DISABLE_DOCKER"] is False:
            self.container_manager = ContainerManager(app)
        else:
            if HAS_DOCKER:
                self.app.logger.warning("Docker was forcefully disabled")
                self.app.logger.warning(
                    "To re-enable docker, set FORCE_DISABLE_DOCKER to false in config.toml"
                )
            else:
                self.app.logger.warning("You do not have docker installed")
                self.app.logger.warning("Challenges requiring docker will not run")
            self.container_manager = None

        self.read_challenges()

    def read_challenges(self):
        self.app.logger.info("Reading challenges")

        related_challenges = defaultdict(list)

        challenge_folders = [
            folder
            for folder in os.listdir(CHALLENGES_DIRECTORY)
            if not folder.startswith(".")
            and os.path.isdir(os.path.join(CHALLENGES_DIRECTORY, folder))
            # Skips directories starting with "." and only scans folders
        ]
        for challenge_id in challenge_folders:
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
                self.app.logger.info(f"{challenge_id}: Creating downloads")
                for entry in os.scandir(downloads_dir):
                    # Skip non-files (i.e. folders)
                    if not entry.is_file():
                        continue

                    # Add file download metadata
                    challenge_data["files"].append(entry.name)

            # Start the challenge's Docker container, if needed
            challenge_data["container"] = {}
            if os.path.exists(container_toml):
                # Skip challenges with containers if Docker isn't installed or was forcefully disabled
                if self.container_manager is None:
                    self.app.logger.warning(
                        f"Skipped challenge '{challenge_id}' requiring docker"
                    )
                    continue

                # Read container metadata
                container_data = self.read_toml_file(container_toml, challenge_id)
                challenge_data["container"] = container_data
                parent = container_data.get("parent")
                if parent:
                    self.app.logger.info(f"{challenge_id}: Parented to '{parent}'")

                    # Store challenge relation in dictionary
                    related_challenges[parent].append(challenge_id)
                elif os.path.exists(container_dir):
                    self.container_manager.run_container(
                        container_data, container_dir, challenge_id
                    )
                else:
                    raise FileNotFoundError(
                        f"{challenge_id}: No container folder found, but container.toml was defined"
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

        # Flatten dictionary into a list where (key, [...values]) -> [key, ...values]
        related_challenges = [[x[0]] + x[1] for x in related_challenges.items()]

        for related_set in related_challenges:
            for related_challenge in related_set:
                # Associate related challenges with each other
                self.challenges[related_challenge]["container"]["related"] = [
                    x for x in related_set if x != related_challenge
                ]

    @staticmethod
    def read_toml_file(file_path, challenge_id):
        if not os.path.exists(file_path):
            filename = os.path.basename(file_path)
            raise FileNotFoundError(
                f"Could not find '{filename}' for challenge '{challenge_id}'"
            )

        with open(file_path, "rb") as file:
            return tomlkit.load(file)

    def solve_challenge(self, id_, user):
        solve = Solve(user_id=user.id, challenge_id=id_)
        db.session.add(solve)
        db.session.commit()

    # Gets the all challenges the user has solved, and how long ago they solved it
    def get_user_solved_challenges(self, solves):
        return [
            {
                "time": solve.time,
                "challenge": self.challenges[solve.challenge_id],
                "challenge_id": solve.challenge_id,
                "time_ago": time_ago(solve.time),
            }
            for solve in solves
        ]

    def get_total_points(self, solves):
        return sum([self.challenges[solve.challenge_id]["points"] for solve in solves])

    def get_top_players(self):
        top_players = [
            {
                "id": user.id,
                "username": user.username,
                "score": self.get_total_points(user.solve),
            }
            for user in db.session.scalars(
                db.select(User).options(db.load_only(User.id, User.username))
            ).all()
        ]
        return sorted(top_players, key=lambda x: x["score"], reverse=True)

    # Gets the datapoints for a profile graph of a specific user id
    def get_user_profile_graph(self, user_id):
        # Get the user
        user = db.session.scalar(
            db.select(User)
            .options(db.load_only(User.id, User.username))
            .where(User.id == user_id)
        )

        # At the start of the CTF, the user has 0 points
        datapoints = [
            {
                "time": self.app.config["CTF_START_TIME"],
                "user": user.username,
                "points": 0,
            }
        ]

        # Fetch solves for the given user, sorted from oldest to newest
        solves = (
            Solve.query.filter(Solve.user_id == user.id)
            .order_by(Solve.time.asc())
            .all()
        )

        # For every solve, add a datapoint
        user_score = 0
        for solve in solves:
            challenge = self.challenges[solve.challenge_id]
            points = challenge["points"]
            user_score += points

            datapoints.append(
                {
                    "time": solve.time.isoformat(),
                    "points": user_score,
                }
            )

        # At the current time, the user has the current number of points
        now = datetime.datetime.now().isoformat()
        datapoints.append(
            {
                "time": now,
                "points": user_score,
            }
        )

        return datapoints

    # Returns the last n recent solves
    def get_recent_solves(self, n, first_blood):
        recent_solves = Solve.query.order_by(Solve.time.desc()).limit(n)
        return [
            {
                "solver": solve.user.username,
                "solver_id": solve.user.id,
                "challenge_id": challenge_anchor_id(
                    self.app.jinja_env, solve.challenge_id
                ),
                "challenge": self.challenges[solve.challenge_id],
                "time": solve.time.isoformat(timespec="milliseconds"),
                "first_blood": solve.id in first_blood,
            }
            for solve in recent_solves
        ]

    def get_leaderboard_chart_data(self, top_user_ids):
        dataset = []
        top_cumulative_scores = {user_id: 0 for user_id in top_user_ids}

        # Fetch solves from the database for the given top users, ordered by from oldest to newest
        solves = (
            Solve.query.filter(Solve.user_id.in_(top_user_ids))
            .order_by(Solve.time.asc())
            .all()
        )

        # At the start of the CTF, all users have 0 points
        for user_id in top_user_ids:
            user = db.session.get(User, user_id)

            dataset.append(
                {
                    "time": self.app.config["CTF_START_TIME"],
                    "user": user.username,
                    "points": 0,
                }
            )

        for solve in solves:
            user_id = solve.user_id
            challenge = self.challenges[solve.challenge_id]
            points = challenge["points"]

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
            user = db.session.get(User, user_id)

            # Add current score
            dataset.append(
                {
                    "time": now,
                    "user": user.username if user else "Unknown",
                    "points": top_cumulative_scores[user_id],
                }
            )

        return dataset
