FROM python:3.8-alpine

STOPSIGNAL SIGINT
EXPOSE 3001

RUN apk update

WORKDIR /church_of_jowett

COPY requirements.txt ./
RUN python3 -m pip install -r requirements.txt

COPY ./src /church_of_jowett/src

COPY run.py ./

CMD ["python3", "run.py"]
