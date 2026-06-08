.DEFAULT_GOAL := help

.PHONY: install lint lint-fix test test-unit test-integration \
        db-migrate db-rollback db-reset \
        shell shell-db shell-redis clean clean-all help

install:
	uv sync

lint:
	uv run ruff check api/
	uv run ruff format --check api/

lint-fix:
	uv run ruff check --fix api/
	uv run ruff format api/

test:
	uv run pytest ../../tests/ -v

test-unit:
	uv run pytest ../../tests/unit/ -v

test-integration:
	uv run pytest ../../tests/integration/ -v

db-migrate:
	uv run alembic upgrade head

db-rollback:
	uv run alembic downgrade -1

db-reset:
	@echo "WARNING: This will drop and recreate the database, losing all data."
	@printf "Are you sure? [y/N] " && read ans && [ "$${ans}" = "y" ] || (echo "Aborted." && exit 1)
	uv run alembic downgrade base
	uv run alembic upgrade head

shell:
	docker compose -f ../../docker-compose.yml exec api /bin/bash

shell-db:
	docker compose -f ../../docker-compose.yml exec postgres psql -U postgres -d videosumm

shell-redis:
	docker compose -f ../../docker-compose.yml exec redis redis-cli

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

clean-all: clean
	rm -rf .venv

help:
	@echo "Available targets:"
	@echo "  install            Install dependencies with uv"
	@echo "  lint               Check code style"
	@echo "  lint-fix           Auto-fix code style issues"
	@echo "  test               Run all tests"
	@echo "  test-unit          Run unit tests only"
	@echo "  test-integration   Run integration tests only"
	@echo "  db-migrate         Apply pending migrations"
	@echo "  db-rollback        Roll back last migration"
	@echo "  db-reset           Drop + recreate + migrate (destructive!)"
	@echo "  shell              Shell into api container"
	@echo "  shell-db           psql shell in postgres container"
	@echo "  shell-redis        redis-cli in redis container"
	@echo "  clean              Remove caches"
	@echo "  clean-all          Remove caches and .venv"
