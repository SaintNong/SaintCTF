CHALLENGES = [
    {
        'name': 'Download file',
        'description': "They said not to click links from strangers right?",
        'category': 'web',
        'difficulty': 'easy',
        'points': 10,
        'hosted_onsite': True,
        'folder': 'download_file',
        'files': [{'name': 'flag.txt'}],
        'flag': 'saint{w0w_y0u_d0wnl04d3d_s0m3th1ng!}'
},
    {
        'name': 'testing123',
        'description': 'insert theoretical cryptography here',
        'category': 'crypto',
        'difficulty': 'easy',
        'points': 16000,
        'hosted_onsite': True,
        'folder': 'testing123',
        'files': [{'name': 'test.txt'}],

        'flag': 'saint{ctf}'


    },
    {
        'name': 'test',
        'description': 'I am a wide boi <br> make me not wide',
        'category': 'web',
        'difficulty': 'HOW TO DO THIS HELPPP',
        'points': 102349830342598,
        'hosted_onsite': False,
        'folder': 'test',
        'files': [{'name': 'haha', 'url': 'https://google.com'}],

        'flag': 'saint{ctf}'
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

