# SaintCTF
![Capture The Flag badge](https://img.shields.io/badge/%F0%9F%9A%A9capture-the_flag-964ae2?style=for-the-badge&labelColor=121212)

SaintCTF is a non-customizable, badly written, custom CTF platform.

## Installation
1. Clone the repo
```bash
git clone https://github.com/SaintNong/SaintCTF
cd SaintCTF
```

2. Make a python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install requirements
```bash
pip3 install -r requirements.txt
```

   - (optional) install Docker if you need containerisation
     ```bash
     pip3 install docker==7.1.0
     ```
> [!NOTE]
> Challenges that require containers will **not** run if Docker is not installed.

4. Run SaintCTF
```bash
python3 app.py
```

## Configuration
To configure your deployment of SaintCTF, simply edit '/instance/config.toml' and restart the server.
Example configuration:
```toml
# The SQLAlchemy database URL.
SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
# The start time for this event, in ISO 8601 format
CTF_START_TIME = "2024-05-31T22:40:18.732776"
# Option to forcibly disable docker containerized challenges
FORCE_DISABLE_DOCKER = true
# Option to reset the database when the server is started.
RESET_DATABASE = false
```
> [!NOTE]
> If the configuration file is not present, please run the server to generate a new one.

## How do I make challenges?
To create challenges, follow these steps:

1. Create a folder in '/challenges/' named after your challenge. (e.g. 'example_challenge')

2. Create the file 'challenge.toml' and copy and paste the example configuration below, then edit the values to suit your challenge.
```toml
name = "Example"
author = "ning"
description = """
This is a great example.
What a great example challenge!
Lets all just sit back and admire how great of an example this is..."""
category = "misc"
difficulty = "easy"
points = 10
flag = "saint{example}"
```
3. If there are any files required to solve your challenge, create folder named '/downloads/' in your challenge directory and place downloadable files there.

4. Your challenge is now ready for deployment. Just run the site and see your challenge in action!

### Challenge docker container (optional)
5. If your challenge requires a docker container to be run, create a container.toml file in your challenge directory.
An example is provided here:
```toml
tag = "example_container"
port = 3001
```

6. Create a folder named '/container/' in your challenge folder
>[!NOTE]
> If 'container.toml' is defined but '/container/' does not exist, the CTF will not run.

7. Place your Dockerfile and your container files in this folder. Be sure to use the same port in your Dockerfile as defined in your 'container.toml'.

8. If docker is installed on your server, then your container will now be automatically deployed whenever the server starts!
