.DEFAULT_GOAL := help

.PHONY: install lint lint-fix test test-unit \
        shell logs clean clean-all help

install:
	uv sync

lint:
	uv run ruff check extractor/
	uv run ruff format --check extractor/

lint-fix:
	uv run ruff check --fix extractor/
	uv run ruff format extractor/

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

shell:
	docker compose -f ../../docker-compose.yml exec ai-video-intelligence-extractor /bin/bash

logs:
	docker compose -f ../../docker-compose.yml logs -f ai-video-intelligence-extractor

clean:
	@printf "Cleaning extractor artefacts...\n"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@printf "✓ Clean complete\n"

clean-all: clean
	rm -rf .venv

help:
	@echo "Available targets:"
	@echo "  install            Install dependencies with uv"
	@echo "  lint               Check code style"
	@echo "  lint-fix           Auto-fix code style issues"
	@echo "  test               Run all tests"
	@echo "  test-unit          Run unit tests only"
	@echo "  shell              Shell into extractor container"
	@echo "  logs               Stream extractor container logs"
	@echo "  clean              Remove caches"
	@echo "  clean-all          Remove caches and .venv"
