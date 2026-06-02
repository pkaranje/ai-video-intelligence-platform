.PHONY: help install lint lint-fix clean clean-all

help:
	@echo "shared/ — Internal package for extractor and worker"
	@echo ""
	@echo "Targets:"
	@echo "  make install       Install dependencies (uv sync)"
	@echo "  make lint          Lint with ruff"
	@echo "  make lint-fix      Auto-fix linting issues"
	@echo "  make clean         Clean __pycache__, .pytest_cache, .ruff_cache"
	@echo "  make clean-all     Clean all build artifacts"
	@echo ""
	@echo "Import boundary rules:"
	@echo "  app/queue/publisher.py → messages.py only"
	@echo "  extractor/ → messages.py + middleware.py"
	@echo "  worker/ → messages.py + middleware.py"
	@echo "  frontend/ → nothing"

install:
	uv sync

lint:
	ruff check .

lint-fix:
	ruff format .
	ruff check --fix .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

clean-all: clean
	rm -rf .venv/ dist/ build/ *.egg-info/
