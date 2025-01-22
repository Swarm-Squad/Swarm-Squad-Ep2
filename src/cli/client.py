import datetime
import signal
import socket
import threading

# Client Configuration
HOST = "127.0.0.1"
PORT = 5050
ADDRESS = (HOST, PORT)
ENCODING = "utf-8"
ADMINS = {"admin": "123", "admin2": "123", "admin3": "123"}


class ChatClient:
    def __init__(self):
        self.socket = None
        self.username = None
        self.running = False
        self.is_admin = False
        self.blocked_users = set()

    def get_timestamp(self):
        """Returns formatted timestamp for logging"""
        return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    def log_message(self, message):
        """Print formatted log message with timestamp"""
        # Add a newline before and after specific messages
        if any(keyword in message for keyword in ["Current users"]):
            print(f"{self.get_timestamp()} {message}")
            print("\n", end="")
        else:
            print(f"{self.get_timestamp()} {message}")

    def handle_receive(self):
        """Handle incoming messages from server"""
        while self.running:
            try:
                message = self.socket.recv(2048).decode(ENCODING)
                if not message:
                    break

                # Handle server messages
                if message in [
                    "BANNED",
                    "YOU WERE BANNED BY AN ADMIN !!",
                    "KICKED",
                    "YOU WERE KICKED BY AN ADMIN !!",
                    "SERVER IS SHUTTING DOWN...",
                ]:
                    self.log_message(f"❌ {message}")
                    self.running = False
                    break

                # Handle authentication
                elif message == "USERNAME?":
                    self.socket.send(self.username.encode(ENCODING))
                    continue
                elif message == "PASSWORD?":
                    password = input("🔑 Enter admin password: ").strip()
                    self.socket.send(password.encode(ENCODING))
                    continue
                elif message in ["USERNAME TAKEN", "WRONG PASSWORD"]:
                    self.log_message(f"❌ {message}")
                    self.running = False
                    break

                # Format different types of messages
                if any(
                    keyword in message
                    for keyword in [
                        "joined the chat",
                        "left the chat",
                        "was banned by",
                        "was kicked by",
                        "was muted by",
                        "was unmuted by",
                    ]
                ):
                    self.log_message(message)
                elif message.startswith(("✅", "⚠️", "🚫", "🔇")):
                    self.log_message(message)
                elif ":" in message:
                    sender, msg = message.split(":", 1)
                    sender = sender.strip()
                    # Skip messages from blocked users
                    if sender in self.blocked_users:
                        continue
                    prefix = "👑" if sender in ADMINS else "👤"
                    self.log_message(f"{prefix} {sender}: {msg}")
                else:
                    self.log_message(message)

            except Exception:
                if self.running:
                    self.log_message("❌ Lost connection to server")
                    self.running = False
                break

    def handle_send(self):
        """Handle sending messages to server"""
        while self.running:
            try:
                message = input("")
                if not self.running:
                    break

                if message.startswith("/"):
                    parts = message[1:].split(maxsplit=1)
                    if len(parts) != 2:
                        self.log_message("⚠️ Usage: /command username")
                        continue

                    command, target = parts[0].lower(), parts[1]

                    # Handle block/unblock commands
                    if command == "block":
                        if target == self.username:
                            self.log_message("⚠️ Cannot block yourself")
                            continue
                        if target in ADMINS and not self.is_admin:
                            self.log_message("⚠️ Cannot block admins")
                            continue
                        self.blocked_users.add(target)
                    elif command == "unblock":
                        if target not in self.blocked_users:
                            self.log_message("⚠️ User is not blocked")
                            continue
                        self.blocked_users.remove(target)
                    elif not self.is_admin:
                        self.log_message("🚫 Only admins can use this command!")
                        continue

                    if command not in [
                        "kick",
                        "ban",
                        "mute",
                        "unmute",
                        "block",
                        "unblock",
                    ]:
                        self.log_message(
                            "❌ Invalid command! Available commands: "
                            + ("/kick, /ban, /mute, /unmute, " if self.is_admin else "")
                            + "/block, /unblock"
                        )
                        continue

                else:
                    message = f"{self.username} : {message}"

                self.socket.send(message.encode(ENCODING))

            except Exception:
                if self.running:
                    self.log_message("❌ Error sending message")
                    self.running = False
                break

    def shutdown(self):
        """Handle graceful shutdown"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass

    def start(self):
        """Start the chat client"""
        print("\n=== 💬 Chat Room Client ===\n")

        # Get username
        self.username = input("👤 Enter username: ").strip()
        self.is_admin = self.username in ADMINS

        try:
            # Connect to server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(ADDRESS)
            self.running = True

            # Start threads
            receive_thread = threading.Thread(target=self.handle_receive)
            receive_thread.daemon = True
            receive_thread.start()

            send_thread = threading.Thread(target=self.handle_send)
            send_thread.daemon = True
            send_thread.start()

            # Setup signal handlers
            signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
            signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())

            # Keep main thread alive
            while self.running:
                if not receive_thread.is_alive() or not send_thread.is_alive():
                    self.running = False
                receive_thread.join(0.1)

        except ConnectionRefusedError:
            self.log_message("❌ Connection refused: Make sure the server is running!")
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
        finally:
            self.shutdown()


if __name__ == "__main__":
    client = ChatClient()
    client.start()
