
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir pipenv

# Dependencies are at project root
COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

# Startup scripts
COPY docker/local/django/entrypoint.sh /entrypoint.sh
COPY docker/local/django/start.sh /start.sh

RUN chmod +x /entrypoint.sh /start.sh

# Django application
WORKDIR /app/backend

ENTRYPOINT ["/entrypoint.sh"]