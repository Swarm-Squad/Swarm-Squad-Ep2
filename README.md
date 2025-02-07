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

1. **Install Node.js using nvm:**
   ```bash
   # Install nvm
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
   
   # Reload shell configuration
   source ~/.bashrc  # or source ~/.zshrc
   
   # Install and use Node.js 22
   nvm install 22
   nvm use 22

   # Install pnpm
   npm install -g pnpm@latest-10
   ```

2. **Install dependencies:**
   ```bash
   cd frontend
   pnpm install
   ```

3. **Run development server:**
   ```bash
   pnpm run dev
   ```
   The frontend will be available at `http://localhost:3000`

<div align="center">
  <h2>🔧 Backend (FastAPI)</h2>
</div>

### Features
- 🔌 WebSocket server for real-time communication
- 🔐 User authentication and session management
- 📤 File upload handling
- 👮 Admin controls and user moderation
- 🗄️ User state management

### Tech Stack
- FastAPI
- Python 3.11+
- WebSockets

### Setup & Installation

1. **Install uv:**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Create and activate virtual environment:**
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   uv pip install -r backend/requirements.txt
   ```

4. **Run the server:**
   ```bash
   cd backend/fastapi
   uv run main.py
   ```
   The backend API will be available at `http://localhost:8000`

<div align="center">
  <h2>🛠️ Development Tools</h2>
</div>

### Code Quality
```bash
cd frontend
pnpm run lint
pnpm run format

cd backend
ruff check
ruff check --select I --fix
ruff format
```

### Pre-commit Hooks
```bash
uv pip install ruff pre-commit
pre-commit install --hook-type commit-msg --hook-type pre-commit --hook-type pre-push
```

<div align="center">
  <h2>📁 Project Structure</h2>
</div>

```
📦Swarm-Squad-Ep2
 ┣ 📂README.assets
 ┃ ┗ 📄banner.png
 ┣ 📂backend
 ┃ ┣ 📂fastapi
 ┃ ┃ ┣ 📄__init__.py
 ┃ ┃ ┣ 📄entities.py
 ┃ ┃ ┣ 📄messages.py
 ┃ ┃ ┣ 📄rooms.py
 ┃ ┃ ┗ 📄websocket.py
 ┃ ┣ 📂static
 ┃ ┃ ┗ 📄favicon.ico
 ┃ ┣ 📂templates
 ┃ ┃ ┗ 📄index.html
 ┃ ┣ 📄__init__.py
 ┃ ┣ 📄database.py
 ┃ ┣ 📄main.py
 ┃ ┣ 📄models.py
 ┃ ┣ 📄schemas.py
 ┃ ┣ 📄utils.py
 ┃ ┗ 📄vehicle_sim.db
 ┣ 📂scripts
 ┃ ┣ 📂utils
 ┃ ┃ ┣ 📄client.py
 ┃ ┃ ┗ 📄message_templates.py
 ┃ ┣ 📄__init__.py
 ┃ ┣ 📄run_simulation.py
 ┃ ┣ 📄simulator.py
 ┃ ┣ 📄test_client.py
 ┃ ┗ 📄visualize_simulation.py
 ┣ 📄__init__.py
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
