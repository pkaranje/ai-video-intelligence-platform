# ==============================================================================
#  AI Video Intelligence Platform — Root Makefile
#  Delegates to service Makefiles via $(MAKE) -C <path> <target>
#  Never duplicates service-level logic.
# ==============================================================================

.DEFAULT_GOAL := help

# ------------------------------------------------------------------------------
# Phony targets
# ------------------------------------------------------------------------------
.PHONY: help
.PHONY: env-check install
.PHONY: lint lint-fix test
.PHONY: build build-no-cache
.PHONY: up up-dev up-api up-frontend up-extractor up-workers
.PHONY: down down-all restart logs
.PHONY: db-migrate db-rollback db-reset
.PHONY: ps health
.PHONY: clean clean-all clean-volumes
.PHONY: shared-% api-% extractor-% worker-% frontend-%

# ------------------------------------------------------------------------------
# Colours
# ------------------------------------------------------------------------------
CYAN  := \033[0;36m
GREEN := \033[0;32m
AMBER := \033[0;33m
RED   := \033[0;31m
RESET := \033[0m

# ------------------------------------------------------------------------------
# Compose command — always v2, never docker-compose (v1)
# ------------------------------------------------------------------------------
COMPOSE := docker compose

# ==============================================================================
#  HELP
# ==============================================================================
help:
	@printf "\n$(CYAN)AI Video Intelligence Platform$(RESET)\n\n"
	@printf "$(GREEN)Setup$(RESET)\n"
	@printf "  env-check           Copy .env.docker.*.example → .env.docker.* if missing\n"
	@printf "  install             Install all deps: shared → api → extractor → worker → frontend\n"
	@printf "\n$(GREEN)Code quality$(RESET)\n"
	@printf "  lint                Ruff check + format check (all Python services)\n"
	@printf "  lint-fix            Ruff check + format with auto-fix\n"
	@printf "  test                Run all tests (unit + integration)\n"
	@printf "\n$(GREEN)Docker — full stack$(RESET)\n"
	@printf "  build               Build all images (uses cache)\n"
	@printf "  build-no-cache      Build all images (no cache)\n"
	@printf "  up                  Start all services detached\n"
	@printf "  up-dev              Start all services with live logs\n"
	@printf "  down                Stop and remove containers\n"
	@printf "  down-all            Stop containers + remove volumes + orphans\n"
	@printf "  restart             Rebuild and restart all services\n"
	@printf "  logs                Tail logs (all services)\n"
	@printf "  ps                  Show running containers\n"
	@printf "  health              Check healthcheck status of all containers\n"
	@printf "\n$(GREEN)Docker — service subsets$(RESET)\n"
	@printf "  up-api              postgres + redis + api (with rebuild)\n"
	@printf "  up-frontend         + frontend\n"
	@printf "  up-extractor        + ffmpeg-extractor\n"
	@printf "  up-workers          full stack — all 10 services\n"
	@printf "\n$(GREEN)Database$(RESET)\n"
	@printf "  db-migrate          alembic upgrade head\n"
	@printf "  db-rollback         alembic downgrade -1\n"
	@printf "  db-reset            Drop + recreate + migrate (destructive)\n"
	@printf "\n$(GREEN)Cleanup$(RESET)\n"
	@printf "  clean               Remove __pycache__, .pytest_cache, .ruff_cache\n"
	@printf "  clean-all           clean + docker image prune\n"
	@printf "  clean-volumes       Remove all named volumes (destructive — data loss)\n"
	@printf "\n$(GREEN)Service-specific (delegates)$(RESET)\n"
	@printf "  shared-<target>     e.g. make shared-lint\n"
	@printf "  api-<target>        e.g. make api-shell, make api-shell-db\n"
	@printf "  extractor-<target>  e.g. make extractor-logs\n"
	@printf "  worker-<target>     e.g. make worker-shell-1, make worker-trigger-cleanup\n"
	@printf "  frontend-<target>   e.g. make frontend-typecheck\n\n"

# ==============================================================================
#  SETUP
# ==============================================================================
env-check:
	@missing=0; \
	for f in db api extractor worker; do \
		if [ ! -f .env.docker.$$f ]; then \
			if [ -f .env.docker.$$f.example ]; then \
				cp .env.docker.$$f.example .env.docker.$$f; \
				printf "$(AMBER)Created .env.docker.$$f — fill in real values before running$(RESET)\n"; \
			else \
				printf "$(RED)Missing .env.docker.$$f.example — cannot create .env.docker.$$f$(RESET)\n"; \
				missing=1; \
			fi \
		fi \
	done; \
	if [ $$missing -eq 1 ]; then exit 1; fi
	@printf "$(GREEN)✓ Env check complete$(RESET)\n"

install: env-check
	@printf "$(CYAN)Installing shared...$(RESET)\n"
	@$(MAKE) -C libs/shared install
	@printf "$(CYAN)Installing api...$(RESET)\n"
	@$(MAKE) -C services/api install
	@printf "$(CYAN)Installing extractor...$(RESET)\n"
	@$(MAKE) -C services/extractor install
	@printf "$(CYAN)Installing worker...$(RESET)\n"
	@$(MAKE) -C services/worker install
	@printf "$(CYAN)Installing frontend...$(RESET)\n"
	@$(MAKE) -C frontend install
	@printf "$(GREEN)✓ All dependencies installed$(RESET)\n"

# ==============================================================================
#  CODE QUALITY
# ==============================================================================
lint:
	@printf "$(CYAN)Linting all services...$(RESET)\n"
	@$(MAKE) -C libs/shared lint
	@$(MAKE) -C services/api lint
	@[ ! -d services/extractor ] || $(MAKE) -C services/extractor lint
	@[ ! -d services/worker ]    || $(MAKE) -C services/worker lint
	@printf "$(GREEN)✓ Lint passed$(RESET)\n"

lint-fix:
	@printf "$(CYAN)Fixing lint issues...$(RESET)\n"
	@[ ! -d libs/shared ] || @$(MAKE) -C libs/shared lint-fix
	@[ ! -d services/api ] || @$(MAKE) -C services/api lint-fix
	@[ ! -d services/extractor ] || $(MAKE) -C services/extractor lint-fix
	@[ ! -d services/worker ]    || $(MAKE) -C services/worker lint-fix
	@printf "$(GREEN)✓ Lint fixed$(RESET)\n"

test:
	@printf "$(CYAN)Running all tests...$(RESET)\n"
	@[ ! -d services/api ] || @$(MAKE) -C services/api test
	@[ ! -d services/extractor ] || $(MAKE) -C services/extractor test
	@[ ! -d services/worker ]    || $(MAKE) -C services/worker test
	@printf "$(GREEN)✓ All tests passed$(RESET)\n"

# ==============================================================================
#  DOCKER — BUILD
# ==============================================================================
build:
	@printf "$(CYAN)Building all images...$(RESET)\n"
	$(COMPOSE) build
	@printf "$(GREEN)✓ Build complete$(RESET)\n"

build-no-cache:
	@printf "$(CYAN)Building all images (no cache)...$(RESET)\n"
	$(COMPOSE) build --no-cache
	@printf "$(GREEN)✓ Build complete$(RESET)\n"

# ==============================================================================
#  DOCKER — RUN
# ==============================================================================
up: env-check
	@printf "$(CYAN)Starting all services...$(RESET)\n"
	$(COMPOSE) up -d --build
	@printf "$(GREEN)✓ All services started$(RESET)\n"
	@printf "  API      → http://localhost:8000/health\n"
	@printf "  UI       → http://localhost:3000\n"
	@printf "  Docs     → http://localhost:8000/docs\n"
	@printf "  DevTrack → http://localhost:8000/__devtrack__/dashboard\n"

up-dev: env-check
	$(COMPOSE) up --build

up-api: env-check
	@printf "$(CYAN)Starting api stack...$(RESET)\n"
	$(COMPOSE) up -d --build postgres redis api
	@printf "$(GREEN)✓ Started: postgres, redis, api$(RESET)\n"
	@printf "  API      → http://localhost:8000/health\n"
	@printf "  Docs     → http://localhost:8000/docs\n"
	@printf "  DevTrack → http://localhost:8000/__devtrack__/dashboard\n"

up-frontend: env-check
	@printf "$(CYAN)Starting frontend stack...$(RESET)\n"
	$(COMPOSE) up -d --build postgres redis api frontend
	@printf "$(GREEN)✓ Started: postgres, redis, api, frontend$(RESET)\n"
	@printf "  UI       → http://localhost:3000\n"
	@printf "  DevTrack → http://localhost:8000/__devtrack__/dashboard\n"

up-extractor: env-check
	@printf "$(CYAN)Starting extractor stack...$(RESET)\n"
	$(COMPOSE) up -d --build postgres redis api ffmpeg-extractor
	@printf "$(GREEN)✓ Started: postgres, redis, api, ffmpeg-extractor$(RESET)\n"
	@printf "  DevTrack → http://localhost:8000/__devtrack__/dashboard\n"

up-workers: env-check
	@printf "$(CYAN)Starting full stack...$(RESET)\n"
	$(COMPOSE) up -d --build
	@printf "$(GREEN)✓ Full stack started (10 services)$(RESET)\n"
	@printf "  API      → http://localhost:8000/health\n"
	@printf "  UI       → http://localhost:3000\n"
	@printf "  DevTrack → http://localhost:8000/__devtrack__/dashboard\n"

down:
	@printf "$(CYAN)Stopping services...$(RESET)\n"
	$(COMPOSE) down
	@printf "$(GREEN)✓ Services stopped$(RESET)\n"

down-all:
	@printf "$(AMBER)Stopping services and removing volumes...$(RESET)\n"
	$(COMPOSE) down -v --remove-orphans
	@printf "$(GREEN)✓ Services stopped, volumes removed$(RESET)\n"

restart: down up

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

health:
	@printf "$(CYAN)Container health status:$(RESET)\n"
	@docker ps --format "table {{.Names}}\t{{.Status}}" \
		--filter "name=ai-video-intelligence"

# ==============================================================================
#  DATABASE
# ==============================================================================
db-migrate:
	@$(MAKE) -C services/api db-migrate

db-rollback:
	@$(MAKE) -C services/api db-rollback

db-reset:
	@printf "$(AMBER)WARNING: This will destroy all data. Press Ctrl+C to cancel...$(RESET)\n"
	@sleep 3
	@$(MAKE) -C services/api db-reset

# ==============================================================================
#  CLEANUP
# ==============================================================================
clean:
	@printf "$(CYAN)Cleaning build artefacts...$(RESET)\n"
	@[ ! -d libs/shared ] || @$(MAKE) -C libs/shared clean
	@[ ! -d services/api ] || @$(MAKE) -C services/api clean
	@[ ! -d services/extractor ] || $(MAKE) -C services/extractor clean
	@[ ! -d services/worker ]    || $(MAKE) -C services/worker clean
	@[ ! -d frontend ] || @$(MAKE) -C frontend clean
	@printf "$(GREEN)✓ Clean complete$(RESET)\n"

clean-all: clean
	@printf "$(CYAN)Pruning Docker images...$(RESET)\n"
	@docker image prune -f
	@printf "$(GREEN)✓ Full cleanup complete$(RESET)\n"

clean-volumes:
	@printf "$(RED)WARNING: This will permanently delete all data volumes.$(RESET)\n"
	@printf "$(RED)Press Ctrl+C to cancel or wait 5 seconds to continue...$(RESET)\n"
	@sleep 5
	$(COMPOSE) down -v
	@printf "$(GREEN)✓ Volumes removed$(RESET)\n"

# ==============================================================================
#  WILDCARD DELEGATION
# ==============================================================================
shared-%:
	@$(MAKE) -C libs/shared $*

api-%:
	@$(MAKE) -C services/api $*

extractor-%:
	@$(MAKE) -C services/extractor $*

worker-%:
	@$(MAKE) -C services/worker $*

frontend-%:
	@$(MAKE) -C frontend $*
