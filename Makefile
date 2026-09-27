.PHONY: install up down migrate migrations run worker beat test cov lint format check superuser shell

install:      ## Install dev dependencies + git hooks
	pip install -r requirements/dev.txt && pre-commit install

up:           ## Start Postgres, Redis, Mailpit
	docker compose up -d

down:
	docker compose down

migrate:
	python manage.py migrate

migrations:
	python manage.py makemigrations

run:
	python manage.py runserver 0.0.0.0:8000

worker:
	celery -A config worker -l info

beat:
	celery -A config beat -l info

test:
	pytest

cov:
	pytest --cov=apps --cov-report=term-missing

lint:
	ruff check . && ruff format --check .

format:
	ruff check --fix . && ruff format .

check:        ## Everything CI runs
	python manage.py check && python manage.py makemigrations --check --dry-run && $(MAKE) lint && $(MAKE) test

superuser:
	python manage.py createsuperuser

shell:
	python manage.py shell
