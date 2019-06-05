# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

RUN apt-get update && apt-get install -y \
        gcc \
        libc-dev \
        libxslt-dev \
        libxml2-dev \
        libffi-dev \
        libssl-dev \
        zip \
        unzip \
        vim \
        && rm -rf /var/lib/apt/lists/*

RUN apt-cache search linux-headers-generic

# Install production dependencies.
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip setuptools six && pip install --no-cache-dir -r requirements.txt

# Copy PyWren proxy to the container image.
ENV APP_HOME /pywrenProxy
WORKDIR $APP_HOME
COPY pywrenproxy.py .

CMD exec gunicorn --bind :$PORT --workers 1 --timeout 600 pywrenproxy:proxy
