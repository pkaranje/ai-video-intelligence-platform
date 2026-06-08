.PHONY: help install lint lint-fix clean clean-all

help:
	@echo "shared — Internal shared library"
	@echo ""
	@echo "Targets:"
	@echo "  install             Install package and dev dependencies (uv sync)"
	@echo "  lint                Run ruff check"
	@echo "  lint-fix            Run ruff fix"
	@echo "  clean               Remove build artifacts"
	@echo "  clean-all           Clean + remove __pycache__ and .venv"
	@echo ""
	@echo "Import Boundary (from CLAUDE.md):"
	@echo ""
	@echo "  Service             May import       What"
	@echo "  ──────────────────  ──────────────   ──────────────────────────"
	@echo "  api/queue/          Yes              messages.py only"
	@echo "  api/ (elsewhere)    No               —"
	@echo "  extractor/          Yes              messages.py + middleware.py"
	@echo "  worker/             Yes              messages.py + middleware.py"
	@echo "  frontend/           No               —"

install:
	uv sync

lint:
	ruff check shared/

lint-fix:
	ruff check --fix shared/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .ruff_cache/ build/ dist/ *.egg-info/ 2>/dev/null || true

clean-all: clean
	rm -rf .venv/

.DEFAULT_GOAL := help
