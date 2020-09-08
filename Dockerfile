FROM python:3.8-alpine

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

RUN adduser --home /app --no-create-home --disabled-password --gecos '' app

RUN mkdir /app/db
RUN mkdir /app/images
RUN mkdir /app/https
RUN chown app:app /app/*
COPY templates /app/templates
COPY src /app/src

WORKDIR /app
USER app

ENTRYPOINT ["src/main.py"]
