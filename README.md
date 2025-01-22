<div align="center">
  <a href="https://github.com/Sang-Buster/Swarm-Squad"><img src="img/banner.png?raw=true" /></a>
  <h1>Episode II: The Digital Dialogue</h1>
  <h6><small>A continuation of our journey into real-time communication with enhanced features and user management.</small></h6>
  <p><b>#Chat Room &emsp; #Real-Time Communication &emsp; #User Management <br/>#Flask &emsp; #Flask-SocketIO &emsp; #Interactive UI</b></p>
</div>


<div align="center">
  <h2 align="center">🔬 Research Evolution</h2>
</div>

* **💬 Real-Time Chat**: Send and receive messages instantly with other users in the chat room.
* **🖼️ Image Sharing**: Easily share images with other users by uploading them from your device.
* **👥 User Management**: The admin panel allows administrators to view connected users, ban, and kick them from the chat room.
* **🚫 Banned Users List**: The admin panel also displays a list of banned users for easy reference.
* **📱 Responsive Design**: The application is designed to be responsive, ensuring a great user experience on devices of all sizes.


<div align="center">
  <h2>🔧 Tech Stack</h2>
</div>

* **Flask**: A lightweight web framework for Python, used to build the backend of the application.
* **Flask-SocketIO**: A Flask extension that adds WebSocket support, enabling real-time communication between the server and clients.
* **JavaScript**: Used to handle user interactions and update the chat interface in real-time.
* **HTML5 & CSS3**: Used to design and structure the user interface, ensuring a visually appealing and intuitive experience.


<div align="center">
  <h2>🛠️ Setup & Installation</h2>
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

3. **Create a virtual environment:**
   ```bash
   uv venv
   ```

4. **Activate the virtual environment:**
   ```bash
   # macOS/Linux
   source .venv/bin/activate
   ```

   ```bash
   # Windows
   .venv\Scripts\activate
   ```

5. **Install the required packages:**
   ```bash
   uv pip install -r requirements.txt
   ```

6. **Install pre-commit:**
   ```bash
   uv pip install ruff pre-commit
   ```
   - `ruff` is a super fast Python linter and formatter.
   - `pre-commit` helps maintain code quality by running automated checks before commits are made.

7. **Install git hooks:**
   ```bash
   pre-commit install --hook-type commit-msg --hook-type pre-commit --hook-type pre-push
   ```

   These hooks perform different checks at various stages:
   - `commit-msg`: Ensures commit messages follow the conventional format
   - `pre-commit`: Runs Ruff linting and formatting checks before each commit
   - `pre-push`: Performs final validation before pushing to remote
  

8. **Code Linting:**
   ```bash
   ruff check
   ruff format
   ```


<div align="center">
  <h2>🌐 Web Usage</h2>
</div>

1. **Run the application:**
   ```bash
   python src/web/app.py
   ```

   - Open your web browser and navigate to `http://localhost:5000` to join the chat room.
   - **For Admin Panel:** Open your web browser and navigate to `http://localhost:5000/admin`



<div align="center">
  <h2>🖥️ CLI  Usage</h2>
</div>

1. **Run the server:**
   ```bash
   python src/cli/server.py
   ```

2. **Run the client:**
   ```bash
   python src/cli/client.py
   ```

   - Enter your username when prompted.
   - If you are an admin, enter the password when prompted.