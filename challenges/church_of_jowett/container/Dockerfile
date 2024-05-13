FROM python:3.8-alpine

RUN apk update

RUN mkdir /church_of_jowett
RUN mkdir /church_of_jowett/src

COPY requirements.txt /church_of_jowett
COPY run.py /church_of_jowett
COPY run.sh /church_of_jowett

COPY ./src /church_of_jowett/src
RUN chmod +x /church_of_jowett/run.sh

WORKDIR /church_of_jowett

EXPOSE 3001

CMD ["sh", "run.sh"]
