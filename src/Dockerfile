FROM python:latest

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/0

RUN mkdir /app
COPY . /app

RUN pip install --upgrade pip && pip install -U poetry

WORKDIR /app

RUN poetry install