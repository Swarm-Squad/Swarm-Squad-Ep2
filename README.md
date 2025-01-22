<div align="center">
  <a href="https://github.com/Sang-Buster/Swarm-Squad"><img src="img/banner.png?raw=true" /></a>
  <h1>Episode II: The Digital Dialogue</h1>
  <h6><small>A continuation of our journey into real-time communication with enhanced features and user management.</small></h6>
  <p><b>#Chat Room &emsp; #Real-Time Communication &emsp; #User Management <br/>#Flask &emsp; #Flask-SocketIO &emsp; #Interactive UI</b></p>
</div>


<div align="center">
  <h2>✨ Features</h2>
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
   git clone https://github.com/your-username/chatroom.git
   cd chatroom
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # macOS/Linux
   source .venv/bin/activate
   ```

   ```bash
   # Windows
   .venv\Scripts\activate
   ```

4. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install pre-commit:**
   ```bash
   pip install pre-commit
   ```

2. **Install git hooks:**
   ```bash
   pre-commit install --hook-type commit-msg --hook-type pre-commit --hook-type pre-push
   ```

3. **Code Linting:**
   ```bash
   ruff check
   ruff format
   ```


<div align="center">
  <h2>🌐 Web Usage</h2>
</div>

1. **Run the application:**
   ```bash
   python web/app.py
   ```
   Open your web browser and navigate to `http://localhost:5000` to join the chat room.
   **For Admin Panel:** Open your web browser and navigate to `http://localhost:5000/admin`



<div align="center">
  <h2>🖥️ CLI  Usage</h2>
</div>

1. **Run the server:**
   ```bash
   python cli/server.py
   ```

2. **Run the client:**
   ```bash
   python cli/client.py
   ```

   - Enter your username when prompted.
   - If you are an admin, enter the password when prompted.