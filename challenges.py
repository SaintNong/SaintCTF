CHALLENGES = [
    {
        'name': 'Download File',
        'author': 'ning',
        'description': "They said not to click links from strangers right?",
        'category': 'misc',
        'difficulty': 'free',
        'points': 15,
        'hosted_onsite': True,
        'folder': 'download_file',
        'files': [{'name': 'flag.txt'}],
        'flag': 'saint{w0w_y0u_d0wnl04d3d_s0m3th1ng!}'
    },
    {
        'name': 'Flag Format',
        'author': 'ning',
        'description': 'Hey, uh I forgot the flag format...\nCould you please find it for me?',
        'category': 'misc',
        'difficulty': 'free',
        'points': 10,
        'hosted_onsite': True,
        'folder': 'flag_format',
        'files': [],

        'flag': 'saint{FLAG_FORMAT}'


    },
]


class ChallengeManager:
    def __init__(self):
        self.challenges = CHALLENGES

        # Replace all newlines in description with the html <br> tags
        for challenge in self.challenges:
            challenge['description'] = challenge['description'].replace('\n', '<br>')

        # Very dirty script to process challenge paths to include the downloads folder
        # 'challenge.txt' => '/downloads/challenge_name/challenge.txt'
        for i, challenge in enumerate(self.challenges):
            if challenge['hosted_onsite']:
                for file_data in challenge['files']:
                    file_data['url'] = f"/downloads/{challenge['folder']}/{file_data['name']}"

