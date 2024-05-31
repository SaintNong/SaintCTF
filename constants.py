import importlib.util

STATIC_DIRECTORY = "static"
CHALLENGES_DIRECTORY = "challenges"
CONFIG_FILE = "config.toml"

DIFFICULTY_MAPPING = {
    "free points": 0,
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "insane": 4,
    "not ok": 5,
}

HAS_DOCKER = importlib.util.find_spec("docker") is not None
