# SnapChronicles command runner (Windows-focused)
# Each target activates `.venv` (fallback `venv`) before running commands.

.PHONY: help check-env install run search view-db test test-db test-vector lint format clean

ACTIVATE = if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) else (call venv\Scripts\activate.bat)

help: ## List available commands.
	@findstr /r /c:"^[a-zA-Z0-9_-][a-zA-Z0-9_-]*:.*## " Makefile

check-env: ## Validate that a Python virtual environment exists and can run Python.
	@cmd /c "$(ACTIVATE) && python --version"

install: ## Install Python dependencies from requirements.txt.
	@cmd /c "$(ACTIVATE) && python -m pip install --upgrade pip && pip install -r requirements.txt"

run: ## Start dual capture (screen OCR + speaker ASR).
	@cmd /c "$(ACTIVATE) && echo [%DATE% %TIME%] [INFO] Starting dual capture && python src\\run_dual_capture.py && echo [%DATE% %TIME%] [INFO] Dual capture stopped"

search: ## Start semantic search CLI.
	@cmd /c "$(ACTIVATE) && python search.py"

view-db: ## Print stored events and database stats.
	@cmd /c "$(ACTIVATE) && python src\\database\\db_viewer.py"

test: ## Run all tests under tests/ with pytest.
	@cmd /c "$(ACTIVATE) && pytest tests"

test-db: ## Run manual database CRUD smoke test.
	@cmd /c "$(ACTIVATE) && python src\\database\\test_db.py"

test-vector: ## Run vectorization integration test.
	@cmd /c "$(ACTIVATE) && python src\\database\\test_vectorization_integration.py"

lint: ## Run Ruff lint checks.
	@cmd /c "$(ACTIVATE) && ruff check src tests"

format: ## Format code with Black.
	@cmd /c "$(ACTIVATE) && black src tests"

clean: ## Remove common local runtime artifacts.
	@cmd /c "if exist snap.db del /q snap.db"
	@cmd /c "if exist vectors.faiss del /q vectors.faiss"
	@cmd /c "if exist __pycache__ rmdir /s /q __pycache__"
