.PHONY: help env-check install lint lint-fix test
.PHONY: build up up-dev up-api up-frontend up-extractor up-workers down restart logs
.PHONY: db-migrate db-rollback db-reset clean clean-all
.PHONY: shared-% api-% extractor-% worker-% frontend-%

help:
	@echo "AI Video Intelligence Platform — Root Makefile"
	@echo ""
	@echo "Installation & Setup:"
	@echo "  env-check           Copy .env.docker.example → .env.docker if missing"
	@echo "  install             Install all dependencies (shared → api → extractor → worker → frontend)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint                Lint all services"
	@echo "  lint-fix            Lint and fix all services"
	@echo "  test                Run tests (api service)"
	@echo ""
	@echo "Docker & Compose:"
	@echo "  build               Build all Docker images"
	@echo "  up                  Start all services (daemon mode)"
	@echo "  up-dev              Start all services (foreground, verbose logs)"
	@echo "  up-api              Start postgres, redis, api"
	@echo "  up-frontend         Start postgres, redis, api, frontend"
	@echo "  up-extractor        Start postgres, redis, api, ffmpeg-extractor"
	@echo "  up-workers          Start full stack (postgres, redis, api, extractor, workers, scheduler)"
	@echo "  down                Stop all services"
	@echo "  restart             Restart all services (down then up)"
	@echo "  logs                Stream logs from all services (ctrl+c to exit)"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate          Run pending migrations"
	@echo "  db-rollback         Rollback last migration"
	@echo "  db-reset            Reset database (drop + create + migrate)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean               Remove build artifacts and caches"
	@echo "  clean-all           Full cleanup + prune Docker images"
	@echo ""
	@echo "Service-specific targets (delegates):"
	@echo "  {shared,api,extractor,worker,frontend}-<target>"
	@echo "    Example: make api-lint-fix, make worker-shell-1"

# ============================================================================
# Installation & Setup
# ============================================================================

env-check:
	@if [ ! -f .env.docker ]; then \
		echo "Creating .env.docker from .env.docker.example..."; \
		cp .env.docker.example .env.docker; \
	else \
		echo ".env.docker already exists"; \
	fi

install: env-check
	$(MAKE) -C libs/shared install
	$(MAKE) -C services/api install
	$(MAKE) -C services/extractor install
	$(MAKE) -C services/worker install
	$(MAKE) -C frontend install
	@echo "✓ All dependencies installed"

# ============================================================================
# Code Quality
# ============================================================================

lint:
	$(MAKE) -C libs/shared lint
	$(MAKE) -C services/api lint
	$(MAKE) -C services/extractor lint
	$(MAKE) -C services/worker lint

lint-fix:
	$(MAKE) -C libs/shared lint-fix
	$(MAKE) -C services/api lint-fix
	$(MAKE) -C services/extractor lint-fix
	$(MAKE) -C services/worker lint-fix

test:
	$(MAKE) -C services/api test

# ============================================================================
# Docker & Compose
# ============================================================================

build:
	docker compose build

up:
	docker compose up -d
	@echo ""
	@echo "✓ Services started in daemon mode"
	@echo "  API:  http://localhost:8000"
	@echo "  UI:   http://localhost:3000"
	@echo "  Use 'make logs' to view logs"

up-dev:
	docker compose up

up-api:
	docker compose up -d postgres redis api
	@echo "✓ postgres, redis, api started"

up-frontend:
	docker compose up -d postgres redis api frontend
	@echo "✓ postgres, redis, api, frontend started"

up-extractor:
	docker compose up -d postgres redis api ffmpeg-extractor
	@echo "✓ postgres, redis, api, ffmpeg-extractor started"

up-workers:
	docker compose up -d
	@echo "✓ Full stack started (postgres, redis, api, extractor, workers, scheduler)"

down:
	docker compose down

restart: down up
	@echo "✓ All services restarted"

logs:
	docker compose logs -f

# ============================================================================
# Database
# ============================================================================

db-migrate:
	$(MAKE) -C services/api db-migrate

db-rollback:
	$(MAKE) -C services/api db-rollback

db-reset:
	$(MAKE) -C services/api db-reset

# ============================================================================
# Cleanup
# ============================================================================

clean:
	$(MAKE) -C libs/shared clean
	$(MAKE) -C services/api clean
	$(MAKE) -C services/extractor clean
	$(MAKE) -C services/worker clean
	$(MAKE) -C frontend clean
	@echo "✓ Cleaned all services"

clean-all: clean
	docker image prune -f
	@echo "✓ Full cleanup complete"

# ============================================================================
# Wildcard Delegation
# ============================================================================

shared-%:
	$(MAKE) -C libs/shared $*

api-%:
	$(MAKE) -C services/api $*

extractor-%:
	$(MAKE) -C services/extractor $*

worker-%:
	$(MAKE) -C services/worker $*

frontend-%:
	$(MAKE) -C frontend $*

.DEFAULT_GOAL := help
