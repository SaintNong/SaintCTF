FROM python:3.8-alpine

STOPSIGNAL SIGINT
EXPOSE 3001

RUN apk update

WORKDIR /grades_grades_grades

COPY requirements.txt ./
RUN python3 -m pip install -r requirements.txt

COPY ./src /grades_grades_grades/src

COPY run.py ./

CMD ["python3", "run.py"]
