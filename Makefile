SHELL := /bin/bash

# ── Service registry (the only block edited when adding a service) ─────
API_DIR   := apps/api
API_PORT  := 45240            # hash-derived base+0 for project "bildung"
API_CMD   := npx wrangler dev --port $(API_PORT)

WEB_DIR   := apps/web
WEB_PORT  := 45241            # base+1
WEB_CMD   := npx vite

DEV_DIR := .dev
PID_DIR := $(DEV_DIR)/pids
LOG_DIR := $(DEV_DIR)/logs
SNAPSHOT_DIR := $(DEV_DIR)/snapshots
API_D1_DIR := $(API_DIR)/.wrangler/state/v3/d1/miniflare-D1DatabaseObject

CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

.PHONY: help install dev start stop status logs build typecheck test test-e2e \
        start-api start-web stop-api stop-web migrate seed reset-db snapshot-db restore-db \
        deploy deploy-api deploy-web clean

##@ General
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(CYAN)Bildungsplattform — make targets$(RESET)\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(GREEN)%-16s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Services
dev: start-api start-web ## Run the full local stack (API + web)
	@printf "$(GREEN)▸ API$(RESET)  http://localhost:$(API_PORT)\n"
	@printf "$(GREEN)▸ Web$(RESET)  http://localhost:$(WEB_PORT)\n"

start: dev ## Alias for dev

start-api: ## Start the API worker
	@mkdir -p $(PID_DIR) $(LOG_DIR)
	@cd $(API_DIR) && $(API_CMD) > ../../$(LOG_DIR)/api.log 2>&1 & echo $$! > $(PID_DIR)/api.pid
	@printf "$(GREEN)started api on :$(API_PORT)$(RESET)\n"

start-web: ## Start the web SPA (Vite)
	@mkdir -p $(PID_DIR) $(LOG_DIR)
	@cd $(WEB_DIR) && $(WEB_CMD) > ../../$(LOG_DIR)/web.log 2>&1 & echo $$! > $(PID_DIR)/web.pid
	@printf "$(GREEN)started web on :$(WEB_PORT)$(RESET)\n"

stop: stop-api stop-web ## Stop all services
stop-api: ## Stop the API worker
	@-kill `cat $(PID_DIR)/api.pid 2>/dev/null` 2>/dev/null; rm -f $(PID_DIR)/api.pid
stop-web: ## Stop the web SPA
	@-kill `cat $(PID_DIR)/web.pid 2>/dev/null` 2>/dev/null; rm -f $(PID_DIR)/web.pid

status: ## Show service status
	@for s in api web; do \
		if kill -0 `cat $(PID_DIR)/$$s.pid 2>/dev/null` 2>/dev/null; then \
			printf "$(GREEN)● %s running$(RESET)\n" $$s; else printf "○ %s stopped\n" $$s; fi; done

logs: ## Tail all service logs
	@tail -f $(LOG_DIR)/*.log

##@ Database
migrate: ## Apply D1 migrations locally
	@cd $(API_DIR) && npx wrangler d1 migrations apply DB --local
seed: ## Seed the local D1
	@cd $(API_DIR) && npx wrangler d1 execute DB --local --file=seed.sql
reset-db: ## Wipe + re-migrate + re-seed the local D1
	@rm -rf $(API_D1_DIR); $(MAKE) migrate seed
snapshot-db: ## Snapshot the local D1 for fast restore
	@mkdir -p $(SNAPSHOT_DIR); rm -rf $(SNAPSHOT_DIR)/api-d1; cp -r $(API_D1_DIR) $(SNAPSHOT_DIR)/api-d1; \
		find $(SNAPSHOT_DIR)/api-d1 -name '*.sqlite-shm' -o -name '*.sqlite-wal' | xargs rm -f
restore-db: ## Restore the last D1 snapshot (<1s)
	@rm -rf $(API_D1_DIR) && cp -r $(SNAPSHOT_DIR)/api-d1 $(API_D1_DIR)

##@ Build & quality
install: ## Install all workspace dependencies
	@npm install
build: ## Build the web SPA
	@cd $(WEB_DIR) && npm run build
typecheck: ## Typecheck both apps
	@cd $(API_DIR) && npm run typecheck
	@cd $(WEB_DIR) && npm run typecheck
test: ## Run API unit tests
	@cd $(API_DIR) && npm test
test-e2e: ## Run web Playwright e2e
	@cd $(WEB_DIR) && npm run test:e2e
clean: stop ## Stop services and remove build artefacts
	@rm -rf $(DEV_DIR) $(WEB_DIR)/dist

##@ Deploy (T2 — see .github/workflows/deploy.yml)
deploy: deploy-api deploy-web ## Deploy both apps to Cloudflare
deploy-api: ## Deploy the API worker
	@cd $(API_DIR) && npx wrangler deploy --var GIT_COMMIT:$(shell git rev-parse --short HEAD)
deploy-web: ## Build + deploy the web SPA
	@cd $(WEB_DIR) && npm run build && npx wrangler deploy
