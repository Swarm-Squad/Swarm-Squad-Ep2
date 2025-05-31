<div align="center">
  <a href="https://github.com/Sang-Buster/Swarm-Squad-Ep2"><img src="https://raw.githubusercontent.com/Swarm-Squad/Swarm-Squad-Ep2/refs/heads/main/lib/banner.png" /></a>
  <h1>Swarm Squad - Episode II: The Digital Dialogue</h1>
  <h6><small>A continuation of our journey into real-time communication with enhanced features and user management.</small></h6>
  <p><b>#Chat Room &emsp; #Real-Time Communication &emsp; #Ollama LLMs <br/>#Next.js &emsp; #WebSocket</b></p>
</div>

<a href="https://github.com/Sang-Buster/Swarm-Squad-Ep2"><img src="https://raw.githubusercontent.com/Swarm-Squad/Swarm-Squad-Ep2/refs/heads/main/lib/screenshot.png" width="100%" /></a>

<h2 align="center">🚀 Getting Started</h2>

It is recommended to use [uv](https://docs.astral.sh/uv/getting-started/installation/) to create a virtual environment and install the following package.

```bash
uv pip install swarm-squad-ep2
```

To run the application, simply type:

```bash
swarm-squad-ep2
# or
swarm-squad-ep2 --help
```

<h2 align="center">🎮 CLI Commands</h2>

The CLI provides several commands to manage the vehicle simulation:

```bash
# Launch both backend (fastapi) and frontend (webui)
swarm-squad-ep2 launch

# Run vehicle simulation (creates real-time data)
swarm-squad-ep2 setup

# Run matplotlib visualization (requires simulation to be running)
swarm-squad-ep2 setup visualize

# Run WebSocket test client (monitor communication)
swarm-squad-ep2 setup test
```

<div align="center">
  <h2>🛠️ Development Installation</h2>
</div>

1. **Clone the repository and navigate to project folder:**

   ```bash
   git clone https://github.com/Sang-Buster/Swarm-Squad-Ep2
   cd Swarm-Squad-Ep2
   ```

2. **Install uv first:**

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   ```bash
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Install the required packages:**
   **Option 1 (recommended):** Synchronizes environment with dependencies in pyproject.toml and uv.lock

   ```bash
   uv sync
   source .venv/bin/activate # .venv\Scripts\activate for Windows
   ```

   **Option 2 (manual):** Manual editable installation without referencing lockfile

   ```bash
   uv venv --python 3.10 # Create virtual environment
   source .venv/bin/activate # .venv\Scripts\activate for Windows
   uv pip install -e .
   ```

<div align="center">
  <h2>👨‍💻 Development Setup</h2>
</div>

1. **Install git hooks:**

   ```bash
   pre-commit install --install-hooks
   ```

   These hooks perform different checks at various stages:

   - `commit-msg`: Ensures commit messages follow the conventional format
   - `pre-commit`: Runs Ruff linting and formatting checks before each commit
   - `pre-push`: Performs final validation before pushing to remote

2. **Code Linting & Formatting:**

   ```bash
   ruff check --fix
   ruff check --select I --fix
   ruff format
   ```

3. **Run the application:**
   ```bash
   uv run src/swarm_squad_ep2/main.py
   ```

<h2 align="center">📁 File Tree</h2>

```
📂Swarm-Squad-Ep2
 ┣ 📂lib
 ┃ ┣ 📄banner.png
 ┃ ┗ 📄screenshot.png
 ┣ 📂src
 ┃ ┗ 📦swarm_squad_ep2
 ┃ ┃ ┣ 📂api
 ┃ ┃ ┃ ┣ 📂routers
 ┃ ┃ ┃ ┃ ┣ 📄batch.py
 ┃ ┃ ┃ ┃ ┣ 📄llms.py
 ┃ ┃ ┃ ┃ ┣ 📄realtime.py
 ┃ ┃ ┃ ┃ ┣ 📄veh2llm.py
 ┃ ┃ ┃ ┃ ┗ 📄vehicles.py
 ┃ ┃ ┃ ┣ 📂static
 ┃ ┃ ┃ ┃ ┗ 📄favicon.ico
 ┃ ┃ ┃ ┣ 📂templates
 ┃ ┃ ┃ ┃ ┗ 📄index.html
 ┃ ┃ ┃ ┣ 📄database.py
 ┃ ┃ ┃ ┣ 📄main.py
 ┃ ┃ ┃ ┣ 📄models.py
 ┃ ┃ ┃ ┣ 📄utils.py
 ┃ ┃ ┃ ┗ 📄vehicle_sim.db
 ┃ ┃ ┣ 📂cli
 ┃ ┃ ┃ ┣ 📄build.py
 ┃ ┃ ┃ ┣ 📄fastapi.py
 ┃ ┃ ┃ ┣ 📄install.py
 ┃ ┃ ┃ ┣ 📄launch.py
 ┃ ┃ ┃ ┣ 📄setup.py
 ┃ ┃ ┃ ┣ 📄utils.py
 ┃ ┃ ┃ ┗ 📄webui.py
 ┃ ┃ ┣ 📂scripts
 ┃ ┃ ┃ ┣ 📂utils
 ┃ ┃ ┃ ┃ ┣ 📄client.py
 ┃ ┃ ┃ ┃ ┗ 📄message_templates.py
 ┃ ┃ ┃ ┣ 📄run_simulation.py
 ┃ ┃ ┃ ┣ 📄simulator.py
 ┃ ┃ ┃ ┣ 📄test_client.py
 ┃ ┃ ┃ ┗ 📄visualize_simulation.py
 ┃ ┃ ┣ 📂web
 ┃ ┃ ┃ ┣ 📂app
 ┃ ┃ ┃ ┃ ┣ 📄globals.css
 ┃ ┃ ┃ ┃ ┣ 📄layout.tsx
 ┃ ┃ ┃ ┃ ┗ 📄page.tsx
 ┃ ┃ ┃ ┣ 📂components
 ┃ ┃ ┃ ┃ ┣ 📂ui
 ┃ ┃ ┃ ┃ ┣ 📄category-header.tsx
 ┃ ┃ ┃ ┃ ┣ 📄chat.tsx
 ┃ ┃ ┃ ┃ ┣ 📄emoji-picker.tsx
 ┃ ┃ ┃ ┃ ┣ 📄message-input.tsx
 ┃ ┃ ┃ ┃ ┣ 📄sidebar.tsx
 ┃ ┃ ┃ ┃ ┣ 📄theme-provider.tsx
 ┃ ┃ ┃ ┃ ┗ 📄theme-toggle.tsx
 ┃ ┃ ┃ ┣ 📂hooks
 ┃ ┃ ┃ ┃ ┣ 📄use-mobile.tsx
 ┃ ┃ ┃ ┃ ┣ 📄use-toast.ts
 ┃ ┃ ┃ ┃ ┗ 📄use-websocket.ts
 ┃ ┃ ┃ ┣ 📂lib
 ┃ ┃ ┃ ┃ ┣ 📄api.ts
 ┃ ┃ ┃ ┃ ┣ 📄mock-data.ts
 ┃ ┃ ┃ ┃ ┗ 📄utils.ts
 ┃ ┃ ┃ ┣ 📂pages
 ┃ ┃ ┃ ┣ 📂public
 ┃ ┃ ┃ ┃ ┗ 📄favicon.ico
 ┃ ┃ ┃ ┣ 📄.eslintrc.json
 ┃ ┃ ┃ ┣ 📄.prettierignore
 ┃ ┃ ┃ ┣ 📄components.json
 ┃ ┃ ┃ ┣ 📄next.config.mjs
 ┃ ┃ ┃ ┣ 📄package.json
 ┃ ┃ ┃ ┣ 📄pnpm-lock.yaml
 ┃ ┃ ┃ ┣ 📄postcss.config.mjs
 ┃ ┃ ┃ ┣ 📄tailwind.config.ts
 ┃ ┃ ┃ ┗ 📄tsconfig.json
 ┃ ┃ ┗ 📄main.py
 ┣ 📄.gitignore
 ┣ 📄.pre-commit-config.yaml
 ┣ 📄.python-version
 ┣ 📄LICENSE
 ┣ 📄README.md
 ┣ 📄pyproject.toml
 ┗ 📄uv.lock
```
