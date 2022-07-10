FROM python:3.10-slim-bullseye

RUN echo 'deb http://deb.debian.org/debian testing main' >> /etc/apt/sources.list
RUN apt update -y
RUN apt install -y gcc

WORKDIR /app

COPY . /app

COPY pyproject.toml poetry.lock /app/

RUN python -m pip install --upgrade pip
RUN pip install "poetry==1.2.0b2"
RUN poetry config virtualenvs.in-project true
RUN poetry install --only main

WORKDIR /app/geogame

CMD poetry run uvicorn main:app --port 8000
