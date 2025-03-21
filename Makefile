.PHONY: install install-frontend install-backend dev frontend backend check_uv check_pnpm check_nvm clean lint lint-frontend lint-backend install-pre-commit

# Check if uv is installed
check_uv:
	@if command -v uv &> /dev/null; then \
		echo "✅ uv is installed."; \
	else \
		echo "❌ uv is not installed."; \
		echo "➡️  Install it by running:"; \
		echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi

# Check if nvm is installed
check_nvm:
	@if command -v nvm &> /dev/null || [ -f "$$HOME/.nvm/nvm.sh" ]; then \
		echo "✅ nvm is installed."; \
	else \
		echo "❌ nvm is not installed."; \
		echo "➡️  Install nvm by running:"; \
		echo "   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"; \
		echo "   Then restart your terminal and run: source ~/.bashrc"; \
		exit 1; \
	fi

# Check if pnpm is installed
check_pnpm:
	@if command -v pnpm &> /dev/null; then \
		echo "✅ pnpm is installed."; \
	else \
		echo "❌ pnpm is not installed."; \
		echo "➡️  Install pnpm by running:"; \
		echo "   npm install -g pnpm@latest-10"; \
		exit 1; \
	fi

# Kill existing server processes
clean:
	@echo "-----------------------------------------------"
	@echo "🧹 Cleaning up processes..."
	@echo "-----------------------------------------------"
	-pkill -f "uvicorn" || true
	-pkill -f "next" || true

# Setup Node.js environment
setup_node: check_nvm
	@echo "-----------------------------------------------"
	@echo "🔧 Setting up Node.js environment..."
	@echo "-----------------------------------------------"
	@. "$$HOME/.nvm/nvm.sh" && nvm install 22 && nvm use 22 && \
	if [ $$? -eq 0 ]; then \
		echo "✅ Node.js 22 is set up successfully."; \
	else \
		echo "❌ Failed to set up Node.js environment."; \
		exit 1; \
	fi

# Install pre-commit hooks
install-pre-commit:
	@echo "-----------------------------------------------"
	@echo "🔧 Installing pre-commit hooks..."
	@echo "-----------------------------------------------"
	@cd backend && source .venv/bin/activate && \
	if ! pre-commit install --hook-type commit-msg --hook-type pre-commit --hook-type pre-push; then \
		echo "❌ Failed to install pre-commit hooks"; \
		exit 1; \
	fi
	@echo "✅ Installed commit-msg hook: Checks commit message format"
	@echo "✅ Installed pre-commit hook: Runs code quality checks before commits"
	@echo "✅ Installed pre-push hook: Runs checks before pushing to remote"

# Install backend dependencies
install-backend: check_uv
	@echo "-----------------------------------------------"
	@echo "📦 Installing backend dependencies..."
	@echo "-----------------------------------------------"
	@cd backend && \
	if ! uv venv; then \
		echo "❌ Failed to create virtual environment"; \
		exit 1; \
	fi && \
	source .venv/bin/activate && \
	if ! uv pip install -r requirements.txt; then \
		echo "❌ Failed to install backend dependencies"; \
		exit 1; \
	fi
	@echo "✅ Backend installation complete!"

# Install frontend dependencies
install-frontend: check_nvm check_pnpm setup_node
	@echo "-----------------------------------------------"
	@echo "📦 Installing frontend dependencies..."
	@echo "-----------------------------------------------"
	@cd frontend && \
	if ! pnpm install; then \
		echo "❌ Failed to install frontend dependencies"; \
		exit 1; \
	fi
	@echo "✅ Frontend installation complete!"

# Install all dependencies
install: install-backend install-frontend install-pre-commit
	@echo "-----------------------------------------------"
	@echo "✅ All installations complete!"
	@echo "-----------------------------------------------"

# Start frontend & backend
dev: clean
	@echo "-----------------------------------------------"
	@echo "🚀 Starting both frontend and backend servers..."
	@echo "-----------------------------------------------"
	@(cd backend/fastapi && \
		if [ ! -d "../.venv" ]; then \
			echo "❌ Virtual environment not found. Run 'make install' first."; \
			exit 1; \
		fi && \
		source ../.venv/bin/activate && \
		uv run main.py) & \
	(cd frontend && \
		if [ ! -d "node_modules" ]; then \
			echo "❌ Node modules not found. Run 'make install' first."; \
			exit 1; \
		fi && \
		pnpm run dev)

# Start frontend only
frontend: clean
	@echo "-----------------------------------------------"
	@echo "🚀 Starting Next.js frontend only..."
	@echo "-----------------------------------------------"
	@cd frontend && \
	if [ ! -d "node_modules" ]; then \
		echo "❌ Node modules not found. Run 'make install' first."; \
		exit 1; \
	fi && \
	pnpm run dev

# Start backend only
backend: clean
	@echo "-----------------------------------------------"
	@echo "🚀 Starting FastAPI backend only..."
	@echo "-----------------------------------------------"
	@cd backend/fastapi && \
	if [ ! -d "../.venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi && \
	source ../.venv/bin/activate && \
	uv run main.py

# Run frontend code quality checks
lint-frontend:
	@echo "-----------------------------------------------"
	@echo "🔍 Running frontend code quality checks..."
	@echo "-----------------------------------------------"
	@cd frontend && \
	if ! pnpm run lint; then \
		echo "❌ Frontend linting failed"; \
		exit 1; \
	fi && \
	if ! pnpm run format; then \
		echo "❌ Frontend formatting failed"; \
		exit 1; \
	fi
	@echo "✅ Frontend code quality checks passed!"

# Run backend code quality checks
lint-backend:
	@echo "-----------------------------------------------"
	@echo "🔍 Running backend code quality checks..."
	@echo "-----------------------------------------------"
	@cd backend && \
	if ! ruff check; then \
		echo "❌ Backend linting failed"; \
		exit 1; \
	fi && \
	if ! ruff check --select I --fix; then \
		echo "❌ Backend import sorting failed"; \
		exit 1; \
	fi && \
	if ! ruff format; then \
		echo "❌ Backend formatting failed"; \
		exit 1; \
	fi
	@echo "✅ Backend code quality checks passed!"

# Run all code quality checks
lint: lint-frontend lint-backend
	@echo "-----------------------------------------------"
	@echo "✅ All code quality checks passed!"
	@echo "-----------------------------------------------"
