FROM python:3.8.1-buster

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY . /app
WORKDIR ./app