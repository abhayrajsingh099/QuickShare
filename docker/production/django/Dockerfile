FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

COPY docker/local/django/entrypoint.sh /entrypoint.sh
COPY docker/local/django/start.sh /start.sh

RUN chmod +x /entrypoint.sh /start.sh

COPY backend/ /app/backend/

WORKDIR /app/backend

ENTRYPOINT ["/entrypoint.sh"]
