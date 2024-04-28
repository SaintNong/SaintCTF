from datetime import datetime

DOWNLOAD_FOLDER = 'downloads'
STATIC_FOLDER = 'static'
""""Here for backup reasons"""
# CHALLENGES = [
#     {
#         'name': 'Download File',
#         'author': 'ning',
#         'description': "They said not to click links from strangers right?",
#         'category': 'misc',
#         'difficulty': 'free',
#         'points': 10,
#         'has_files': True,
#         'folder': 'download_file',
#         'files': [{'name': 'flag.txt'}],
# 
#         'flag': 'saint{w0w_y0u_d0wnl04d3d_s0m3th1ng!}',
#         'solvers': []
#     },
#     {
#         'name': 'Flag Format',
#         'author': 'ning',
#         'description': 'Hey, uh I forgot the flag format...\nCould you please find it for me?',
#         'category': 'misc',
#         'difficulty': 'free',
#         'points': 10,
#         'has_files': True,
#         'folder': 'flag_format',
#         'files': [],
# 
#         'flag': 'saint{FLAG_FORMAT}',
#         'solvers': []
#     },
#     {
#         'name': 'Exam revision',
#         'author': 'ning',
#         'description': 'can you crack this very secure cipher for me??\nThe flag is nvdio{nxnv_xdkczm}',
#         'category': 'misc',
#         'difficulty': 'easy',
#         'points': 15,
#         'has_files': True,
#         'folder': 'exam_revision',
#         'files': [],
# 
#         'flag': 'saint{scsa_cipher}',
#         'solvers': []
#     },
#     {
#         'name': 'Robots? Where???',
#         'author': 'ning',
#         'description': 'Where are the robots???\nSomeone told me there would be robots 😭😭😭😭',
#         'category': 'web',
#         'difficulty': 'easy',
#         'points': 30,
#         'has_files': True,
#         'folder': 'robots',
#         'files': [],
# 
#         'flag': 'saint{I_FOUND_THE_ROBOTS_a3d7cb3}',
#         'solvers': []
# 
#     },
#     {
#         'name': 'Mysterious file',
#         'author': 'ning',
#         'description': 'Anyone here got linux?',
#         'category': 'rev',
#         'difficulty': 'medium',
#         'points': 100,
#         'has_files': True,
#         'folder': 'rev1',
#         'files': [{'name': 'mystery'}],
# 
#         'flag': 'saint{woah_its_a_binary!}',
#         'solvers': []
# 
#     },
#     {
#         'name': 'Very secure censorship',
#         'author': 'alex',
#         'description': 'This flag contains top secret information,\nso I decided to pixelate it.',
#         'category': 'misc',
#         'difficulty': 'hard',
#         'points': 200,
#         'has_files': True,
#         'folder': 'depixelation',
#         'files': [{'name': 'redacted.png'}],
# 
#         'flag': 'saint{unr3d4ct3d}',
#         'solvers': []
# 
#     },
# ]
CHALLENGES_FILE_PATH = 'challenges.json'
RESET_DATA = True

CTF_START_TIME = datetime.now()
