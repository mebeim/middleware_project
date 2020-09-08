FROM python:3.8-alpine

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

RUN adduser --home /app --no-create-home --disabled-password --gecos '' app
RUN mkdir -p /app/images && chown app:app /app/images
WORKDIR /app
USER app

ENTRYPOINT ["src/main.py"]
