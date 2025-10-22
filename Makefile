.PHONY: help start stop restart clean clean-all logs backend frontend install dev status

# Colors for terminal output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(CYAN)Pretty Please - RAG Pipeline$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install all dependencies (Python + Node)
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	python3 -m pip install -r requirements.txt
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd frontend && bun install
	@echo "$(GREEN)Installation complete!$(NC)"

dev: start ## Alias for 'start' - starts all services in development mode

start: ## Start all services (backend + frontend)
	@echo "$(GREEN)Starting Pretty Please services...$(NC)"
	@echo "$(CYAN)Starting backend server on port 8000...$(NC)"
	@python3 -m uvicorn src.jina_rag_pipeline.api.app:app --reload --port 8000 > /tmp/pretty_please_backend.log 2>&1 & echo $$! > /tmp/pretty_please_backend.pid
	@sleep 2
	@echo "$(CYAN)Starting frontend server...$(NC)"
	@cd frontend && bun run dev > /tmp/pretty_please_frontend.log 2>&1 & echo $$! > /tmp/pretty_please_frontend.pid
	@sleep 2
	@echo "$(GREEN)Services started!$(NC)"
	@echo ""
	@echo "$(YELLOW)Backend:$(NC)  http://localhost:8000"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:5173"
	@echo "$(YELLOW)API Docs:$(NC) http://localhost:8000/docs"
	@echo ""
	@echo "Run '$(CYAN)make logs$(NC)' to view logs"
	@echo "Run '$(CYAN)make stop$(NC)' to stop services"

backend: ## Start only the backend server
	@echo "$(GREEN)Starting backend server on port 8000...$(NC)"
	@python3 -m uvicorn src.jina_rag_pipeline.api.app:app --reload --port 8000

frontend: ## Start only the frontend server
	@echo "$(GREEN)Starting frontend server...$(NC)"
	@cd frontend && bun run dev

stop: ## Stop all running services
	@echo "$(YELLOW)Stopping Pretty Please services...$(NC)"
	@if [ -f /tmp/pretty_please_backend.pid ]; then \
		kill `cat /tmp/pretty_please_backend.pid` 2>/dev/null || true; \
		rm /tmp/pretty_please_backend.pid; \
		echo "$(GREEN)Backend stopped$(NC)"; \
	fi
	@if [ -f /tmp/pretty_please_frontend.pid ]; then \
		kill `cat /tmp/pretty_please_frontend.pid` 2>/dev/null || true; \
		rm /tmp/pretty_please_frontend.pid; \
		echo "$(GREEN)Frontend stopped$(NC)"; \
	fi
	@pkill -f "uvicorn.*8000" 2>/dev/null || true
	@pkill -f "bun run dev" 2>/dev/null || true
	@echo "$(GREEN)All services stopped$(NC)"

restart: stop start ## Restart all services

status: ## Check status of services
	@echo "$(CYAN)Service Status:$(NC)"
	@echo ""
	@echo -n "Backend:  "
	@if pgrep -f "uvicorn.*8000" > /dev/null; then \
		echo "$(GREEN)Running$(NC)"; \
	else \
		echo "$(RED)Stopped$(NC)"; \
	fi
	@echo -n "Frontend: "
	@if pgrep -f "bun run dev" > /dev/null; then \
		echo "$(GREEN)Running$(NC)"; \
	else \
		echo "$(RED)Stopped$(NC)"; \
	fi
	@echo ""

logs: ## Show logs from all services
	@echo "$(CYAN)Showing logs (press Ctrl+C to exit)...$(NC)"
	@echo ""
	@tail -f /tmp/pretty_please_backend.log /tmp/pretty_please_frontend.log 2>/dev/null || echo "$(YELLOW)No logs found. Services may not be running.$(NC)"

logs-backend: ## Show backend logs only
	@tail -f /tmp/pretty_please_backend.log 2>/dev/null || echo "$(YELLOW)No backend logs found$(NC)"

logs-frontend: ## Show frontend logs only
	@tail -f /tmp/pretty_please_frontend.log 2>/dev/null || echo "$(YELLOW)No frontend logs found$(NC)"

clean: ## Clean all database and upload data
	@echo "$(RED)WARNING: This will delete all collections and database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python3 cleanup_all_data.py; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

clean-all: stop ## Stop services and clean all data
	@echo "$(RED)WARNING: This will stop all services and delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf .chroma_db chroma_db chroma_storage src/.chroma_db uploads; \
		rm -f /tmp/pretty_please_*.log /tmp/pretty_please_*.pid; \
		echo "$(GREEN)All data and logs cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

test: ## Run fast tests (unit + API + storage)
	@echo "$(GREEN)Running fast tests...$(NC)"
	@pytest tests/unit/ tests/test_api.py tests/test_api_ingestion.py tests/test_storage.py -v

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	@pytest tests/integration/ -v

test-all: ## Run all tests (including slow model-loading tests)
	@echo "$(GREEN)Running all tests...$(NC)"
	@pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@pytest tests/unit/ tests/test_api.py tests/test_api_ingestion.py tests/test_storage.py tests/integration/ --cov=src --cov-report=html --cov-report=term

format: ## Format code with black and prettier
	@echo "$(GREEN)Formatting Python code...$(NC)"
	@black src/ tests/
	@echo "$(GREEN)Formatting frontend code...$(NC)"
	@cd frontend && bunx prettier --write src/

lint: ## Lint code
	@echo "$(GREEN)Linting Python code...$(NC)"
	@ruff check src/ tests/
	@echo "$(GREEN)Linting frontend code...$(NC)"
	@cd frontend && bunx eslint src/

build: ## Build frontend for production
	@echo "$(GREEN)Building frontend...$(NC)"
	@cd frontend && bun run build
	@echo "$(GREEN)Build complete!$(NC)"
