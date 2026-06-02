.PHONY: help env-check install lint lint-fix test test-unit test-integration build up up-dev up-app up-frontend up-extractor up-workers down restart logs db-migrate db-rollback db-reset clean clean-all

help:
	@echo "AI Video Intelligence Platform — Makefile targets"
	@echo ""
	@echo "Setup:"
	@echo "  make env-check              Create .env and .env.docker from examples"
	@echo "  make install                Install deps for all services (shared → app → extractor → worker → frontend)"
	@echo ""
	@echo "Development:"
	@echo "  make lint                   Lint all Python services (shared, app, extractor, worker)"
	@echo "  make lint-fix               Auto-fix linting issues"
	@echo "  make test                   Run all tests (app)"
	@echo "  make test-unit              Run unit tests"
	@echo "  make test-integration       Run integration tests"
	@echo ""
	@echo "Docker:"
	@echo "  make build                  Build all Docker images"
	@echo "  make up                     Start full stack (detached)"
	@echo "  make up-dev                 Start full stack (with logs)"
	@echo "  make up-app                 Start api, postgres, redis only"
	@echo "  make up-frontend            Start frontend only"
	@echo "  make up-extractor           Start extractor only"
	@echo "  make up-workers             Start worker pool + scheduler"
	@echo "  make down                   Stop all services"
	@echo "  make restart                Restart all services"
	@echo "  make logs                   Follow logs from all services"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate             Run pending migrations"
	@echo "  make db-rollback            Rollback last migration"
	@echo "  make db-reset               Reset database (drop + recreate)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                  Clean build artifacts and caches"
	@echo "  make clean-all              Deep clean (includes node_modules, .venv)"
	@echo ""
	@echo "Service-specific targets:"
	@echo "  make shared-<target>        Run 'make <target>' in shared/"
	@echo "  make app-<target>           Run 'make <target>' in app/"
	@echo "  make extractor-<target>     Run 'make <target>' in extractor/"
	@echo "  make worker-<target>        Run 'make <target>' in worker/"
	@echo "  make frontend-<target>      Run 'make <target>' in frontend/"

env-check:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
	fi
	@if [ ! -f .env.docker ]; then \
		cp .env.docker.example .env.docker; \
		echo "Created .env.docker from .env.docker.example"; \
	fi

install: env-check
	$(MAKE) -C shared install
	$(MAKE) -C app install
	$(MAKE) -C extractor install
	$(MAKE) -C worker install
	$(MAKE) -C frontend install

lint:
	$(MAKE) -C shared lint
	$(MAKE) -C app lint
	$(MAKE) -C extractor lint
	$(MAKE) -C worker lint

lint-fix:
	$(MAKE) -C shared lint-fix
	$(MAKE) -C app lint-fix
	$(MAKE) -C extractor lint-fix
	$(MAKE) -C worker lint-fix

test:
	$(MAKE) -C app test

test-unit:
	$(MAKE) -C app test-unit

test-integration:
	$(MAKE) -C app test-integration

build:
	docker compose build

up:
	docker compose up -d

up-dev:
	docker compose up

up-app:
	docker compose up -d postgres redis api

up-frontend:
	docker compose up -d frontend

up-extractor:
	docker compose up -d ffmpeg-extractor

up-workers:
	docker compose up -d worker-1 worker-2 worker-3 worker-4 scheduler

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

db-migrate:
	$(MAKE) -C app db-migrate

db-rollback:
	$(MAKE) -C app db-rollback

db-reset:
	$(MAKE) -C app db-reset

clean:
	$(MAKE) -C shared clean
	$(MAKE) -C app clean
	$(MAKE) -C extractor clean
	$(MAKE) -C worker clean
	$(MAKE) -C frontend clean

clean-all:
	$(MAKE) -C shared clean-all
	$(MAKE) -C app clean-all
	$(MAKE) -C extractor clean-all
	$(MAKE) -C worker clean-all
	$(MAKE) -C frontend clean-all

# Wildcard delegation: make app-shell → cd app && make shell
shared-%:
	$(MAKE) -C shared $*

app-%:
	$(MAKE) -C app $*

extractor-%:
	$(MAKE) -C extractor $*

worker-%:
	$(MAKE) -C worker $*

frontend-%:
	$(MAKE) -C frontend $*
