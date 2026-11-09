COMPOSE = docker compose -f local.yml

# Build and start containers
build:
	$(COMPOSE) up --build -d --remove-orphans

# Start existing containers
up:
	$(COMPOSE) up -d

# Stop and remove containers
down:
	$(COMPOSE) down

# Stop containers and delete volumes (database data will be lost)
down-v:
	$(COMPOSE) down -v

# Validate Compose configuration
config:
	$(COMPOSE) config

# Django migrations
makemigrations:
	$(COMPOSE) run --rm api python manage.py makemigrations

migrate:
	$(COMPOSE) run --rm api python manage.py migrate

# Static files
collectstatic:
	$(COMPOSE) run --rm api python manage.py collectstatic --no-input --clear

# Django admin
superuser:
	$(COMPOSE) run --rm api python manage.py createsuperuser

# Database management
flush:
	$(COMPOSE) run --rm api python manage.py flush

# Inspect Docker network
network-inspect:
	docker network inspect quickshare_quickshare_local_nw

# PostgreSQL shell
db:
	$(COMPOSE) exec postgres psql --username=quickshare --dbname=quickshare

# Logs
logs:
	$(COMPOSE) logs -f

api-logs:
	$(COMPOSE) logs -f api

nginx-logs:
	$(COMPOSE) logs -f nginx

db-logs:
	$(COMPOSE) logs -f postgres

# Container status
ps:
	$(COMPOSE) ps