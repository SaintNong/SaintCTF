from datetime import datetime

DOWNLOAD_DIRECTORY = 'downloads'
STATIC_DIRECTORY = 'static'
CHALLENGES_DIRECTORY = 'challenges'

# Will reset data on each run time
RESET_DATA = True

DIFFICULTY_MAPPING = {
    'free points': 0,
    'easy': 1,
    'medium': 2,
    'hard': 3,
    'insane': 4,
    'not ok': 5,
}


CTF_START_TIME = datetime.now()
