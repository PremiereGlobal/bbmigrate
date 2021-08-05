FROM python:3.9-slim

RUN apt-get update && \
apt-get dist-upgrade -y && \
apt-get install -y --no-install-recommends git curl && \
rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app
ADD bbmigrate /app/bbmigrate
ADD setup.py /app/
ADD README.md /app/
ADD Pipfile /app/
ADD Pipfile.lock /app/
RUN pip install .

ENV BBMIGRATE_IN_DOCKER=true
CMD bbmigrate
