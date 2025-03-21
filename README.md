<div align="center">
  <a href="https://github.com/Sang-Buster/Swarm-Squad"><img src="README.assets/banner.png?raw=true" /></a>
  <h1>Swarm Squad - Episode II: The Digital Dialogue</h1>
  <h6><small>A continuation of our journey into real-time communication with enhanced features and user management.</small></h6>
  <p><b>#Chat Room &emsp; #Real-Time Communication &emsp; #Ollama LLMs <br/>#Next.js &emsp; #WebSocket</b></p>
</div>

<div align="center">
  <h2>🎨 Frontend (Next.js)</h2>
</div>

### Features
- 🌗 Dark/Light mode support
- 📱 Responsive design
- 🎨 Modern UI with Shadcn/UI components
- 🔄 Real-time chat interface
- 🖼️ Image sharing capabilities
- 👥 User management interface
- 🚫 Admin panel with ban/kick functionality

### Tech Stack
- Next.js 14
- TypeScript
- Tailwind CSS
- Shadcn/UI Components
- Socket.io Client

### Setup & Installation

1. **Install Prerequisites:**
   ```bash
   # Install nvm (Node Version Manager)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

   # Reload shell configuration
   source ~/.bashrc  # or source ~/.zshrc

   # Install uv (Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install pnpm (Node.js package manager)
   npm install -g pnpm@latest-10
   ```

2. **Install Project Dependencies:**
   ```bash
   # Install everything (both frontend and backend + pre-commit hooks)
   make install

   # Or install components individually:
   make install-frontend    # Install frontend dependencies only
   make install-backend     # Install backend dependencies only
   make install-pre-commit  # Install pre-commit hooks only
   ```

3. **Start Development Servers:**
   ```bash
   # Start both frontend and backend
   make dev

   # Or start them individually:
   make frontend  # Start only frontend
   make backend   # Start only backend
   ```
   The frontend will be available at `http://localhost:3000`
   The backend API will be available at `http://localhost:8000`

4. **Development Tools:**
   ```bash
   # Run all code quality checks
   make lint

   # Or run them individually:
   make lint-frontend  # Lint and format frontend only
   make lint-backend   # Lint and format backend only

   # Clean up running processes
   make clean
   ```

### Pre-commit Hooks
The project uses several pre-commit hooks to ensure code quality:

- **Commit Message Hook**: Ensures commit messages follow the project's format
- **Pre-commit Hook**: Runs code quality checks before commits
- **Pre-push Hook**: Runs checks before pushing to remote
- **Additional Hooks**:
  - `check-yaml`: Validates YAML file formatting
  - `end-of-file-fixer`: Ensures files end with a newline
  - `trailing-whitespace`: Removes trailing whitespace
  - `ruff`: Lints and formats Python code
  - `eslint`: Lints and formats JavaScript/TypeScript code

These hooks are automatically installed when running `make install` or can be installed separately with `make install-pre-commit`.

<div align="center">
  <h2>📁 Project Structure</h2>
</div>

```
📦Swarm-Squad-Ep2
 ┣ 📂README.assets
 ┃ ┗ 📄banner.png
 ┣ 📂backend
 ┃ ┣ 📂fastapi
 ┃ ┃ ┣ 📂routers
 ┃ ┣ ┣ 📂static
 ┃ ┣ ┣ 📂templates
 ┃ ┣ ┗ 📄main.py
 ┃ ┣ 📂scripts
 ┃ ┃ ┣ 📂utils
 ┃ ┃ ┣ 📄run_simulation.py
 ┃ ┃ ┣ 📄test_client.py
 ┃ ┃ ┗ 📄visualize_simulation.py
 ┗ 📄requirements.txt
 ┣ 📂frontend
 ┃ ┣ 📂app
 ┃ ┣ 📂components
 ┃ ┣ 📂hooks
 ┃ ┣ 📂lib
 ┃ ┣ 📂public
 ┃ ┣ 📄.eslintrc.json
 ┃ ┣ 📄.npmrc
 ┃ ┣ 📄components.json
 ┃ ┣ 📄next-env.d.ts
 ┃ ┣ 📄next.config.mjs
 ┃ ┣ 📄package.json
 ┃ ┣ 📄pnpm-lock.yaml
 ┃ ┣ 📄postcss.config.mjs
 ┃ ┣ 📄tailwind.config.ts
 ┃ ┗ 📄tsconfig.json
 ┣ 📄.gitignore
 ┣ 📄.pre-commit-config.yaml
 ┣ 📄.pre-commit_msg_template.py
 ┣ 📄LICENSE
 ┗ 📄README.md
```
