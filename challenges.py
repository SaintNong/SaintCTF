import constants
import datetime
from datetime import timedelta


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


class Solve:
    def __init__(self, username, time, challenge_id):
        self.username = username
        self.time = time
        self.challenge_id = challenge_id

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
        solve = Solve(user.username, datetime.datetime.now(), index)
        self.challenges[index]['solvers'].append(user.username)
        self.recent_solves.insert(0, solve)

    # Gets the all challenges the user has solved, and how long ago they solved it
    def get_solved_challenges(self, username):
        solved_challenges = []

        for solve in self.recent_solves:
            if solve.username == username:
                solved_challenges.append({
                    "time": solve.time,
                    "challenge": self.challenges[solve.challenge_id],
                    "time_ago": time_ago(solve.time)
                })

        return solved_challenges

    # Returns the last n recent solves
    def get_recent_solves(self, n):
        recent_solves = []
        for solve in self.recent_solves:
            challenge = self.challenges[solve.challenge_id]
            recent_solves.append({
                "solver": solve.username,
                "challenge": challenge,
                "time": solve.time,
                "time_ago": time_ago(solve.time)
            })

            if len(recent_solves) == n:
                break

        return recent_solves

    def get_time_based_leaderboard(self, top_users):
        dataset = []

        top_cumulative_scores = {}
        for user in top_users:
            top_cumulative_scores[user] = 0

        # Go from the oldest solve to the lgatest one
        for solve in self.recent_solves[::-1]:
            if solve.username in top_users:
                username = solve.username
                solved_challenge = self.challenges[solve.challenge_id]
                weight = solved_challenge['points']

                # The instant before this solve, they were at the score they were at before
                dataset.append({
                    "time": (solve.time-timedelta(milliseconds=1)).isoformat(),
                    "user": solve.username,
                    "points": top_cumulative_scores[username],
                })

                # The instant when they solve the challenge, they jump up to however many points the
                # challenge was worth
                top_cumulative_scores[username] += weight
                dataset.append({
                    "time": solve.time.isoformat(),
                    "user": solve.username,
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
