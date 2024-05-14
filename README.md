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
     pip3 install docker==7.0.0
     ```
> [!NOTE]
> Challenges that require containers will **not** run if Docker is not installed.

4. Run SaintCTF
```bash
python3 app.py
```


