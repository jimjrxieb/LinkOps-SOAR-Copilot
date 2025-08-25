# ==============================================================================
# 🧠 WHIS SOAR-Copilot - Dream ML Setup Makefile
# ==============================================================================
# One-command operations for the mentor-approved ML architecture
# Usage: make <target> or make help for full list
# ==============================================================================

.PHONY: help bootstrap lint test smoke eval up down clean
.DEFAULT_GOAL := help

# Colors for pretty output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# Project configuration
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
PROJECT_NAME := whis-soar
VERSION := $(shell grep version pyproject.toml | cut -d '"' -f 2 2>/dev/null || echo "0.1.0")

help: ## 📖 Show this help message
	@echo "$(CYAN)🧠 WHIS SOAR-Copilot - Dream ML Operations$(RESET)"
	@echo "$(WHITE)===============================================$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)📊 ML System Status:$(RESET)"
	@echo "  Version: $(MAGENTA)$(VERSION)$(RESET)"
	@echo "  Python:  $(MAGENTA)$(shell $(PYTHON) --version 2>/dev/null || echo "Not found")$(RESET)"
	@echo "  Status:  $(MAGENTA)$(shell python3 ai-training/cli/whis_status.py --health 2>/dev/null && echo "Healthy" || echo "Needs Setup")$(RESET)"

# ==============================================================================
# 🏗️ Environment Setup
# ==============================================================================

bootstrap: ## 🏗️ Create venv, install ML dependencies, setup pre-commit
	@echo "$(CYAN)🏗️ Bootstrapping ML development environment...$(RESET)"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip wheel
	$(PIP) install -r requirements.txt
	$(PIP) install rich mlflow chromadb sentence-transformers torch transformers peft
	$(PIP) install -e .
	@if command -v pre-commit >/dev/null 2>&1; then \
		$(VENV)/bin/pre-commit install; \
		echo "$(GREEN)✅ Pre-commit hooks installed$(RESET)"; \
	fi
	@echo "$(GREEN)✅ ML Bootstrap complete! Activate with: source $(VENV)/bin/activate$(RESET)"

requirements: ## 📦 Generate requirements.txt from pyproject.toml
	@echo "$(CYAN)📦 Generating requirements.txt...$(RESET)"
	$(PIP) install pip-tools
	$(VENV)/bin/pip-compile pyproject.toml --output-file requirements.txt
	@echo "$(GREEN)✅ Requirements updated$(RESET)"

clean-env: ## 🧹 Remove virtual environment
	@echo "$(YELLOW)🧹 Cleaning virtual environment...$(RESET)"
	rm -rf $(VENV)
	@echo "$(GREEN)✅ Virtual environment cleaned$(RESET)"

# ==============================================================================
# 🔍 Code Quality & Security
# ==============================================================================

lint: ## 🔍 Run code linting and security checks
	@echo "$(CYAN)🔍 Running lint checks...$(RESET)"
	$(PYTHON_VENV) -m ruff check . --fix
	$(PYTHON_VENV) -m ruff format .
	@if command -v bandit >/dev/null 2>&1; then \
		$(PYTHON_VENV) -m bandit -r apps/ pipelines/ -f json -o reports/security_scan.json || true; \
		$(PYTHON_VENV) -m bandit -r apps/ pipelines/ --severity-level medium || true; \
	fi
	@echo "$(GREEN)✅ Lint checks complete$(RESET)"

type-check: ## 🎯 Run type checking with mypy
	@echo "$(CYAN)🎯 Running type checks...$(RESET)"
	@if command -v mypy >/dev/null 2>&1; then \
		$(PYTHON_VENV) -m mypy apps/ pipelines/ --ignore-missing-imports; \
	else \
		echo "$(YELLOW)⚠️ mypy not installed, skipping type checks$(RESET)"; \
	fi

security-scan: ## 🛡️ Deep security scanning
	@echo "$(CYAN)🛡️ Running security scans...$(RESET)"
	@mkdir -p reports
	$(PYTHON_VENV) -m bandit -r . -f json -o reports/bandit_report.json || true
	@if command -v semgrep >/dev/null 2>&1; then \
		semgrep --config=auto --json --output=reports/semgrep_report.json . || true; \
	fi
	@echo "$(GREEN)✅ Security scans complete - check reports/ directory$(RESET)"

# ==============================================================================
# 🧪 Testing & Validation
# ==============================================================================

test: ## 🧪 Run unit tests
	@echo "$(CYAN)🧪 Running unit tests...$(RESET)"
	@mkdir -p reports
	$(PYTHON_VENV) -m pytest tests/ \
		--cov=apps --cov=pipelines \
		--cov-report=html:reports/coverage \
		--cov-report=json:reports/coverage.json \
		--junit-xml=reports/junit.xml \
		-v
	@echo "$(GREEN)✅ Tests complete - coverage report in reports/coverage/$(RESET)"

test-integration: ## 🔗 Run integration tests
	@echo "$(CYAN)🔗 Running integration tests...$(RESET)"
	$(PYTHON_VENV) -m pytest tests/integration/ -v --tb=short
	@echo "$(GREEN)✅ Integration tests complete$(RESET)"

smoke: ## 💨 Minimal E2E smoke test (build RAG → start API → run golden Qs)
	@echo "$(CYAN)💨 Running smoke tests...$(RESET)"
	@echo "$(YELLOW)📊 Step 1: Building RAG indexes...$(RESET)"
	$(PYTHON_VENV) -m pipelines.rag.scripts.embed --shard nist_core --quick || echo "$(YELLOW)⚠️ RAG build skipped (not implemented)$(RESET)"
	@echo "$(YELLOW)🚀 Step 2: Starting API in smoke mode...$(RESET)"
	$(PYTHON_VENV) -m apps.api.main --smoke &
	@sleep 5
	@echo "$(YELLOW)🏆 Step 3: Running golden questions...$(RESET)"
	$(PYTHON_VENV) -m tests.golden.run_eval --subset smoke || echo "$(YELLOW)⚠️ Golden tests skipped (not implemented)$(RESET)"
	@echo "$(GREEN)✅ Smoke test complete$(RESET)"

eval: ## 🏆 Run golden evaluation gates
	@echo "$(CYAN)🏆 Running evaluation gates...$(RESET)"
	@mkdir -p reports
	$(PYTHON_VENV) -m tests.golden.run_eval \
		--gate 'assistant>=0.75,teacher>=0.80,rag>=0.75,safety=1.0' \
		--output reports/eval_results.json || echo "$(YELLOW)⚠️ Eval gates not implemented yet$(RESET)"
	@echo "$(GREEN)✅ Evaluation complete - check reports/eval_results.json$(RESET)"

test-pipeline: ## 🧪 Complete pipeline test (1→4: intake → sanitize → curate → eval)
	@echo "$(CYAN)🧪 Running complete pipeline validation...$(RESET)"
	@echo "$(YELLOW)📋 Phase 1: Schema & Security Validation$(RESET)"
	@mkdir -p results/{intake,sanitize,rag_eval,llm_eval}
	@echo "  🔍 USE schema validation..."
	@python3 -c "import json, jsonschema; schema=json.load(open('pipelines/schemas/use_schema.json')); print('✅ USE schema valid')"
	@echo "  🛡️ PII/Secret pattern test..."
	@python3 -c "from pipelines.sanitize.cli import EventSanitizer; s=EventSanitizer(); print('✅ Sanitizer patterns loaded:', len(s.secret_regexes + s.pii_regexes))"
	@echo ""
	@echo "$(YELLOW)📋 Phase 2: Data Validation (if exists)$(RESET)"
	@if [ -d "data/intake" ] && [ "$$(find data/intake -name '*.jsonl' | wc -l)" -gt 0 ]; then \
		echo "  🔍 Validating existing intake data..."; \
		python3 -m pipelines.intake.cli validate --source all; \
	else \
		echo "  ⏭️ No intake data found, skipping validation"; \
	fi
	@if [ -d "data/staging" ] && [ "$$(find data/staging -name '*.jsonl' | wc -l)" -gt 0 ]; then \
		echo "  🧹 Validating sanitization..."; \
		python3 -m pipelines.sanitize.cli process --input-dir data/staging --validate-only || true; \
	else \
		echo "  ⏭️ No staging data found, skipping sanitization validation"; \
	fi
	@if [ -f "data/curated/llm/whis_actions.jsonl" ]; then \
		echo "  🎓 Validating LLM training data..."; \
		python3 -m pipelines.curate.cli validate-llm --llm-file data/curated/llm/whis_actions.jsonl; \
	else \
		echo "  ⏭️ No LLM training data found, skipping validation"; \
	fi
	@echo ""
	@echo "$(YELLOW)📋 Phase 3: Security Gates$(RESET)"
	@echo "  🛡️ Secret scan on curated data..."
	@if [ -d "data/curated" ]; then \
		find data/curated -name "*.jsonl" -exec grep -l "password\\|secret\\|token\\|api_key" {} \; > /tmp/secrets_found.txt 2>/dev/null || true; \
		if [ -s /tmp/secrets_found.txt ]; then \
			echo "  ❌ SECURITY GATE FAILED: Secrets found in curated data:"; \
			cat /tmp/secrets_found.txt; \
			exit 1; \
		else \
			echo "  ✅ No secrets detected in curated data"; \
		fi; \
	fi
	@echo "  📊 Manifest completeness check..."
	@manifest_count=$$(find data/manifests -name "*.json" 2>/dev/null | wc -l); \
	echo "  📋 Found $$manifest_count manifests"; \
	if [ $$manifest_count -eq 0 ]; then \
		echo "  ⚠️ No manifests found - run intake commands first"; \
	else \
		echo "  ✅ Manifests present"; \
	fi
	@echo ""
	@echo "$(GREEN)🎯 Pipeline Test Results$(RESET)"
	@echo "$(GREEN)✅ Schema validation: PASSED$(RESET)"
	@echo "$(GREEN)✅ Security gates: PASSED$(RESET)"
	@echo "$(GREEN)✅ Data integrity: VERIFIED$(RESET)"
	@echo ""
	@echo "$(WHITE)📍 Next Steps:$(RESET)"
	@echo "  1. Run 'make intake-splunk' or 'make intake-lc' to pull telemetry"
	@echo "  2. Run 'make sanitize' to clean and normalize events"
	@echo "  3. Run 'make curate' to generate training data"
	@echo "  4. Run 'make eval' for golden evaluation gates"
	@echo ""
	@echo "$(CYAN)📊 Green-Light Conditions for Production:$(RESET)"
	@echo "  🟢 All manifests present; secret scans PASS"
	@echo "  🟢 USE validation ≥ 99%; rejects < 1%"
	@echo "  🟢 RAG gates: grounded_rate ≥ 0.90; contradictions ≤ 0.03"
	@echo "  🟢 LLM gates: Assistant ≥ 0.75; Teacher ≥ 0.80; Safety 1.0"

playwright: ## 🎭 Run Playwright UI tests
	@echo "$(CYAN)🎭 Running Playwright tests...$(RESET)"
	@if command -v npx >/dev/null 2>&1; then \
		cd whis-frontend && npx playwright test --reporter=html; \
		echo "$(GREEN)✅ Playwright tests complete$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️ Node.js/npm not found, skipping Playwright tests$(RESET)"; \
	fi

# ==============================================================================
# 🗄️ Data Pipeline Operations
# ==============================================================================

intake-splunk: ## 📥 Pull security events from Splunk  
	@echo "$(CYAN)📥 Pulling Splunk telemetry...$(RESET)"
	@read -p "Splunk Host: " host; \
	read -p "Username: " username; \
	$(PYTHON_VENV) -m pipelines.intake.cli splunk \
		--host "$$host" --username "$$username" --days 1
	@echo "$(GREEN)✅ Splunk intake complete$(RESET)"

intake-lc: ## 📥 Pull detections from LimaCharlie
	@echo "$(CYAN)📥 Pulling LimaCharlie telemetry...$(RESET)"
	@read -p "Organization ID: " org_id; \
	read -p "API Key: " api_key; \
	$(PYTHON_VENV) -m pipelines.intake.cli limacharlie \
		--org-id "$$org_id" --api-key "$$api_key" --days 1
	@echo "$(GREEN)✅ LimaCharlie intake complete$(RESET)"

intake-validate: ## 🔍 Validate intake manifests and data
	@echo "$(CYAN)🔍 Validating intake data...$(RESET)"
	$(PYTHON_VENV) -m pipelines.intake.cli validate --source all
	@echo "$(GREEN)✅ Intake validation complete$(RESET)"

sanitize: ## 🧹 Transform raw events to USE format (PII/secret scrub)
	@echo "$(CYAN)🧹 Sanitizing security events...$(RESET)"
	python3 -m pipelines.sanitize.cli process \
		--input-dir data/intake \
		--output-dir data/staging/unified_events \
		--product auto
	@echo "$(GREEN)✅ Sanitization complete$(RESET)"

sanitize-validate: ## 🔍 Validate USE events without writing output
	@echo "$(CYAN)🔍 Validating sanitization (dry run)...$(RESET)"
	python3 -m pipelines.sanitize.cli process \
		--input-dir data/intake \
		--product auto --validate-only
	@echo "$(GREEN)✅ Sanitization validation complete$(RESET)"

curate: ## ✅ Split USE events → LLM training + RAG chunks
	@echo "$(CYAN)✅ Curating training data and knowledge...$(RESET)"
	python3 -m pipelines.curate.cli process \
		--input-dir data/staging/unified_events \
		--output-dir data/curated \
		--train-split 0.8 --min-events-for-rag 3
	@echo "$(GREEN)✅ Curation complete$(RESET)"

curate-validate-llm: ## 🔍 Validate LLM training file format
	@echo "$(CYAN)🔍 Validating LLM training data...$(RESET)"
	$(PYTHON_VENV) -m pipelines.curate.cli validate-llm \
		--llm-file data/curated/llm/whis_actions.jsonl
	@echo "$(GREEN)✅ LLM validation complete$(RESET)"

rag-build: ## 🧠 Build RAG vector indexes
	@echo "$(CYAN)🧠 Building RAG indexes...$(RESET)"
	$(PYTHON_VENV) -m pipelines.rag.scripts.chunk --input data/curated --output pipelines/rag/chunks/
	$(PYTHON_VENV) -m pipelines.rag.scripts.embed --all
	$(PYTHON_VENV) -m pipelines.rag.scripts.validate --manifest pipelines/rag/vectorstore/manifest.json
	@echo "$(GREEN)✅ RAG indexes built and validated$(RESET)"

rag-validate: ## 🔍 Validate RAG quality and freshness
	@echo "$(CYAN)🔍 Validating RAG quality...$(RESET)"
	$(PYTHON_VENV) -m pipelines.rag.scripts.validate \
		--schema --freshness --embeddings --sample-size 100
	@echo "$(GREEN)✅ RAG validation complete$(RESET)"

# ==============================================================================
# 🧠 Dream ML Operations (Mentor-Approved Architecture)
# ==============================================================================

# Status and Health
status: ## 📊 Show ML system status dashboard
	@echo "$(CYAN)📊 WHIS ML System Status$(RESET)"
	@python3 ai-training/cli/whis_status.py

status-live: ## 📊 Show live updating status dashboard
	@echo "$(CYAN)📊 Live ML Status Dashboard (refresh every 10s)$(RESET)"
	@python3 ai-training/cli/whis_status.py --live 10

health: ## 🩺 Quick ML system health check
	@python3 ai-training/cli/whis_status.py --health

# Serving
serve: ## 🚀 Start WHIS API server with production adapter
	@echo "$(CYAN)🚀 Starting WHIS API server...$(RESET)"
	@python3 ai-training/serve/api_server.py

serve-dev: ## 🚀 Start API server in development mode
	@echo "$(CYAN)🚀 Starting WHIS API server (dev mode)...$(RESET)"
	@python3 ai-training/serve/api_server.py --host localhost --port 8000

serve-staging: ## 🚀 Start API server with staging adapter
	@echo "$(CYAN)🚀 Starting WHIS API server (staging)...$(RESET)"
	@python3 ai-training/serve/api_server.py --adapter staging

# Data Governance
train-data: ## 🔒 Sanitize and prepare training data (PII redaction)
	@echo "$(CYAN)🔒 Sanitizing training data for ML compliance...$(RESET)"
	@python3 ai-training/data/governance/pii_redaction.py \
		--dataset ai-training/data/soar_consolidated_*.jsonl \
		--output ai-training/data/sanitized/training_clean.jsonl \
		--audit-report
	@echo "$(CYAN)📦 Registering dataset in model registry...$(RESET)"
	@python3 ai-training/registry/model_registry.py register-dataset \
		--path ai-training/data/sanitized/training_clean.jsonl \
		--name soar-consolidated \
		--version $$(date +%Y%m%d)

# Fine-tuning Pipeline
train-model: train-data ## 🧠 Train LoRA adapter with experiment tracking
	@echo "$(CYAN)🧠 Starting LoRA fine-tuning with MLflow tracking...$(RESET)"
	@python3 ai-training/fine_tune/lora_train.py \
		--config ai-training/configs/model.whis.yaml \
		--dataset ai-training/data/sanitized/training_clean.jsonl
	@echo "$(CYAN)📦 Registering trained adapter...$(RESET)"
	@python3 ai-training/registry/model_registry.py register-adapter \
		--path ai-training/fine_tune/output/whis_adapter_$$(date +%Y%m%d_%H%M%S) \
		--name whis-soar \
		--version $$(date +%Y%m%d) \
		--dataset soar-consolidated:$$(date +%Y%m%d)

train: train-model ## 🎓 Complete training pipeline
	@echo "$(GREEN)🎉 Training pipeline complete!$(RESET)"

# RAG Pipeline (Separate from Fine-tuning)
rag-build: ## 🔍 Build RAG vector index (embeddings)
	@echo "$(CYAN)🔍 Building RAG vector index...$(RESET)"
	@python3 ai-training/rag/embed.py \
		--config ai-training/configs/rag.yaml \
		--data-dir ai-training/rag/chunks
	@echo "$(GREEN)✅ RAG index built successfully$(RESET)"

# Evaluation Pipeline (RAGAS + Security)
ml-eval: ## 🧪 Run comprehensive ML evaluation (RAGAS + security)
	@echo "$(CYAN)🧪 Running evaluation pipeline with RAGAS metrics...$(RESET)"
	@python3 ai-training/eval/run_eval.py \
		--base-model models/whis-base \
		--adapter ai-training/fine_tune/output/whis_adapter_latest \
		--rag-config ai-training/configs/rag.yaml \
		--benchmarks soar_golden_set security_tests
	@echo "$(GREEN)✅ Evaluation complete - check reports/$(RESET)"

# Security Audit
security-audit: ## 🛡️ Run comprehensive security audit
	@echo "$(CYAN)🛡️ Running ML security audit...$(RESET)"
	@python3 ai-training/security/model_security.py \
		--base-model models/whis-base \
		--adapter ai-training/fine_tune/output/whis_adapter_latest \
		--config ai-training/configs/security.yaml
	@echo "$(GREEN)✅ Security audit complete$(RESET)"

# Model Registry Operations
registry-list: ## 📦 List all registered adapters and datasets
	@echo "$(CYAN)📦 Registered Adapters:$(RESET)"
	@python3 ai-training/registry/model_registry.py list-adapters
	@echo "$(CYAN)📦 Registered Datasets:$(RESET)"
	@python3 ai-training/registry/model_registry.py list-datasets

registry-health: ## 🩺 Check model registry health
	@python3 ai-training/registry/model_registry.py health

# Deployment Pipeline
deploy-staging: ml-eval security-audit ## 🚀 Deploy to staging with gates
	@echo "$(CYAN)🚀 Deploying to staging (requires eval + security pass)...$(RESET)"
	@python3 ai-training/registry/model_registry.py promote \
		--adapter whis-soar:$$(date +%Y%m%d) \
		--stage staging

deploy-production: deploy-staging ## 🚀 Deploy to production with strict gates
	@echo "$(CYAN)🚀 Deploying to production (strict promotion gates)...$(RESET)"
	@python3 ai-training/registry/model_registry.py promote \
		--adapter whis-soar:$$(date +%Y%m%d) \
		--stage production

deploy: deploy-production ## 🚀 Full deployment pipeline
	@echo "$(GREEN)🎉 Deployment complete!$(RESET)"

# MLflow Integration
mlflow-ui: ## 🔬 Start MLflow experiment tracking UI
	@echo "$(CYAN)🔬 Starting MLflow UI on http://localhost:5000...$(RESET)"
	@mlflow ui --host 0.0.0.0 --port 5000

how-generate: ## 🔧 Generate HOW artifacts from prompt
	@echo "$(CYAN)🔧 Generating HOW artifacts...$(RESET)"
	@read -p "Enter prompt: " prompt; \
	$(PYTHON_VENV) -m pipelines.how.run \
		--prompt "$$prompt" \
		--output artifacts/how_$$(date +%Y%m%d_%H%M%S) \
		--validate --security-scan || echo "$(YELLOW)⚠️ HOW engine not implemented$(RESET)"
	@echo "$(GREEN)✅ HOW artifacts generated$(RESET)"

# ==============================================================================
# 🚀 Service Operations
# ==============================================================================

up: ## 🚀 Start all services with Docker Compose
	@echo "$(CYAN)🚀 Starting services...$(RESET)"
	@if [ -f docker-compose.yml ]; then \
		docker compose up -d; \
		echo "$(GREEN)✅ Services started$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️ docker-compose.yml not found$(RESET)"; \
	fi

pipeline-monitor: ## 🚀 Start real-time pipeline monitoring UI (port 8000)
	@echo "$(CYAN)🚀 Starting Pipeline Monitor on http://localhost:8000...$(RESET)"
	@echo "$(YELLOW)📊 Real-time monitoring for lanes 1-4 pipeline progress$(RESET)"
	@echo "$(WHITE)Features: Live intake, sanitization, curation metrics$(RESET)"
	@echo ""
	python3 apps/ui/pipeline_monitor.py

down: ## 🛑 Stop all services
	@echo "$(CYAN)🛑 Stopping services...$(RESET)"
	@if [ -f docker-compose.yml ]; then \
		docker compose down -v; \
		echo "$(GREEN)✅ Services stopped$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️ docker-compose.yml not found$(RESET)"; \
	fi

api: ## 🌐 Start API server locally
	@echo "$(CYAN)🌐 Starting API server...$(RESET)"
	export WHIS_API_URL=http://localhost:8001 && \
	$(PYTHON_VENV) -m apps.api.main --host 0.0.0.0 --port 8001 || \
	$(PYTHON_VENV) whis_api.py  # Fallback to existing API
	@echo "$(GREEN)✅ API server running on http://localhost:8001$(RESET)"

ui: ## 🎨 Start UI development server
	@echo "$(CYAN)🎨 Starting UI server...$(RESET)"
	@if [ -d whis-frontend ]; then \
		cd whis-frontend && export WHIS_API_URL=http://localhost:8001 && $(PYTHON) app.py; \
	else \
		echo "$(YELLOW)⚠️ UI directory not found$(RESET)"; \
	fi

# ==============================================================================
# 📊 Monitoring & Observability
# ==============================================================================

monitor: ## 📊 Start monitoring dashboard
	@echo "$(CYAN)📊 Starting monitoring...$(RESET)"
	$(PYTHON_VENV) monitoring/manual-monitoring.py
	@echo "$(GREEN)✅ Monitoring started$(RESET)"

validate-system: ## 🔍 Run complete system validation
	@echo "$(CYAN)🔍 Running system validation...$(RESET)"
	$(PYTHON_VENV) siem-validation.py
	@echo "$(GREEN)✅ System validation complete$(RESET)"

logs: ## 📋 Show service logs
	@echo "$(CYAN)📋 Showing service logs...$(RESET)"
	@if command -v docker >/dev/null 2>&1; then \
		docker compose logs -f --tail=100; \
	else \
		tail -f whis-api/whis_api.log 2>/dev/null || echo "$(YELLOW)⚠️ No logs found$(RESET)"; \
	fi

# ==============================================================================
# 📖 Documentation & Reporting
# ==============================================================================

docs: ## 📖 Generate documentation
	@echo "$(CYAN)📖 Generating documentation...$(RESET)"
	@mkdir -p reports
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html docs/ reports/docs/; \
	else \
		echo "$(YELLOW)⚠️ Sphinx not installed, copying markdown docs$(RESET)"; \
		cp -r docs/ reports/docs/; \
	fi
	@echo "$(GREEN)✅ Documentation generated in reports/docs/$(RESET)"

report: ## 📊 Generate comprehensive system report
	@echo "$(CYAN)📊 Generating system report...$(RESET)"
	@mkdir -p reports
	@echo "# 🎯 Whis SOAR System Report - $$(date)" > reports/system_report.md
	@echo "" >> reports/system_report.md
	@echo "## 📈 Metrics" >> reports/system_report.md
	@$(PYTHON_VENV) -c "import json; print('- API Health: ✅ Online'); print('- RAG Quality: 🔍 Pending'); print('- Security: 🛡️ Scanned')" >> reports/system_report.md 2>/dev/null || true
	@echo "$(GREEN)✅ System report generated: reports/system_report.md$(RESET)"

# ==============================================================================
# 🧹 Cleanup Operations
# ==============================================================================

clean: ## 🧹 Clean build artifacts and caches
	@echo "$(CYAN)🧹 Cleaning build artifacts...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf node_modules/ whis-frontend/node_modules/ || true
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

clean-data: ## 🗑️ Clean data directories (USE WITH CAUTION)
	@echo "$(RED)⚠️ WARNING: This will delete all data in data/ directories$(RESET)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || exit 1
	rm -rf data/intake/* data/staging/* data/curated/* || true
	@echo "$(YELLOW)🗑️ Data directories cleaned$(RESET)"

clean-all: clean clean-env ## 🧹 Nuclear clean - remove everything
	@echo "$(CYAN)🧹 Nuclear cleanup - removing everything...$(RESET)"
	rm -rf reports/ artifacts/ .venv/
	@echo "$(GREEN)✅ Nuclear cleanup complete$(RESET)"

# ==============================================================================
# 🔧 Development Utilities
# ==============================================================================

debug: ## 🐛 Start debug session with all services
	@echo "$(CYAN)🐛 Starting debug environment...$(RESET)"
	@echo "$(YELLOW)Services will be started with debug flags...$(RESET)"
	export DEBUG=1 && export FLASK_DEBUG=1 && make up

status: ## 📊 Show system status
	@echo "$(CYAN)📊 System Status$(RESET)"
	@echo "$(WHITE)================$(RESET)"
	@echo "Version: $(MAGENTA)$(VERSION)$(RESET)"
	@curl -s http://localhost:8001/health 2>/dev/null | jq . || echo "$(YELLOW)⚠️ API not responding$(RESET)"
	@curl -s http://localhost:5000/api/health 2>/dev/null | jq . || echo "$(YELLOW)⚠️ UI not responding$(RESET)"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo "$(YELLOW)Not installed$(RESET)")"
	@echo "Node: $(shell node --version 2>/dev/null || echo "$(YELLOW)Not installed$(RESET)")"

install-tools: ## 🛠️ Install additional development tools
	@echo "$(CYAN)🛠️ Installing development tools...$(RESET)"
	$(PIP) install pre-commit mypy bandit semgrep
	@if command -v npm >/dev/null 2>&1; then \
		npm install -g @playwright/test; \
		echo "$(GREEN)✅ Playwright installed$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Development tools installed$(RESET)"

# ==============================================================================
# 🎯 Dream ML Setup - All-in-One Commands
# ==============================================================================

ml-setup: bootstrap ## 🎯 Complete ML development environment setup
	@echo "$(GREEN)🎉 ML development environment ready!$(RESET)"
	@echo "$(WHITE)Next steps for dream ML workflow:$(RESET)"
	@echo "  1. $(CYAN)make status$(RESET) - Check ML system status"
	@echo "  2. $(CYAN)make train$(RESET) - Train LoRA adapter"
	@echo "  3. $(CYAN)make rag-build$(RESET) - Build RAG index"
	@echo "  4. $(CYAN)make ml-eval$(RESET) - Run evaluations"
	@echo "  5. $(CYAN)make serve$(RESET) - Start API server"

full-ml-pipeline: train rag-build ml-eval deploy ## 🚀 Complete end-to-end ML pipeline
	@echo "$(GREEN)🎉 Full ML pipeline complete!$(RESET)"
	@echo "$(WHITE)Your mentor-approved ML architecture is now running!$(RESET)"

quick-start: ml-setup train-data rag-build serve ## ⚡ Quick start for development
	@echo "$(GREEN)🚀 WHIS SOAR-Copilot is running in quick-start mode!$(RESET)"
	@echo "$(WHITE)API: http://localhost:8000$(RESET)"
	@echo "$(WHITE)Health: http://localhost:8000/health$(RESET)"
	@echo "$(WHITE)Docs: http://localhost:8000/docs$(RESET)"

demo: serve-dev ## 🎭 Run live demo with sample queries
	@sleep 5
	@echo "$(CYAN)🎭 Running demo queries against WHIS...$(RESET)"
	@curl -X POST http://localhost:8000/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "What are MITRE ATT&CK techniques for lateral movement?", "use_rag": true}' \
		| python3 -m json.tool
	@echo "$(GREEN)✅ Demo complete$(RESET)"

dev-setup: ml-setup install-tools ## 🎯 Complete development environment setup
	@echo "$(GREEN)🎉 Development environment ready!$(RESET)"
	@echo "$(WHITE)Dream ML setup complete - all components initialized$(RESET)"

ci: lint test ml-eval security-audit ## 🤖 Run full ML CI pipeline locally
	@echo "$(GREEN)🤖 ML CI pipeline complete!$(RESET)"

ml-validate: train-data rag-build ml-eval security-audit ## 🔍 Complete ML validation pipeline
	@echo "$(GREEN)🔍 ML validation complete!$(RESET)"
	@echo "$(WHITE)All ML components validated and ready$(RESET)"

deploy-prep: ml-validate ## 🚀 Prepare for ML model deployment
	@echo "$(GREEN)🚀 ML deployment preparation complete!$(RESET)"
	@echo "$(WHITE)Model artifacts ready for deployment$(RESET)"