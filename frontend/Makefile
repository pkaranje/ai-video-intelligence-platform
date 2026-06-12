.PHONY: install dev build typecheck lint lint-fix shell logs clean clean-all help

install:
	npm ci

dev:
	npm run dev

build:
	npm run build

typecheck:
	npx tsc --noEmit

lint:
	npx next lint

lint-fix:
	npx next lint --fix

shell:
	docker exec -it ai-video-intelligence-frontend sh

logs:
	docker logs -f ai-video-intelligence-frontend

clean:
	rm -rf .next out

clean-all: clean
	rm -rf node_modules

help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | awk -F: '{print $$1}' | sort
