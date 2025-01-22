import datetime
import select
import signal
import socket
import sys
import threading

# Server Configuration
HOST = "127.0.0.1"
PORT = 5050
ENCODING = "utf-8"
ADDRESS = (HOST, PORT)

# User Management
ADMINS = {"admin": "123", "admin2": "123", "admin3": "123"}
BANNED_USERS = []
MUTED_USERS = set()
clients = []
usernames = []
blocked_users = {}  # Dictionary to track who blocked whom: {blocker: set(blocked_users)}


def get_timestamp():
    """Returns formatted timestamp for logging"""
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def log_message(message):
    """Print formatted log message with timestamp"""
    # Add a newline before and after specific messages
    if any(keyword in message for keyword in ["connected", "Active users"]):
        print(f"{get_timestamp()} {message}")
        print("\n", end="")
    else:
        print(f"{get_timestamp()} {message}")


def check_client_connection(client):
    """Test if client is still connected"""
    try:
        # Send empty string to test connection
        client.send(b"")
        return True
    except socket.error:
        return False


def broadcast(message, sender_username=None):
    """Broadcast message to all connected clients, respecting blocks"""
    disconnected_clients = []
    for client in clients:
        if not check_client_connection(client):
            disconnected_clients.append(client)
            continue

        receiver_username = usernames[clients.index(client)]

        # Skip sending if receiver has blocked the sender
        if (
            sender_username
            and receiver_username in blocked_users
            and sender_username in blocked_users[receiver_username]
        ):
            continue

        try:
            client.send(message)
        except socket.error:
            disconnected_clients.append(client)

    # Handle any disconnected clients found during broadcast
    for client in disconnected_clients:
        handle_client_disconnect(client)


def disconnect_client(client, message=None):
    """Safely disconnect a client with optional message"""
    try:
        if message:
            client.send(message.encode(ENCODING))
        client.close()
    except socket.error:
        pass


def handle_client_disconnect(client):
    """Handle client disconnection cleanly"""
    if client in clients:
        index = clients.index(client)
        username = usernames[index]

        # Clean up blocked users
        if username in blocked_users:
            del blocked_users[username]
        for blocker in blocked_users:
            if username in blocked_users[blocker]:
                blocked_users[blocker].remove(username)

        # Remove from active lists
        clients.remove(client)
        usernames.remove(username)

        # Remove from muted users if they were muted
        if username in MUTED_USERS:
            MUTED_USERS.remove(username)

        try:
            client.close()
        except:  # noqa:E722
            pass

        # Broadcast user left message and current user list
        broadcast(f"👋 {username} left the chat...".encode(ENCODING))
        broadcast(f"📊 Current users: {', '.join(usernames)}".encode(ENCODING))

        log_message(f"👋 User '{username}' disconnected")
        log_message(f"📊 Active users: {', '.join(usernames)}")


def handle_block_command(client, sender_username, target_user):
    """Handle blocking a user"""
    if target_user not in usernames:
        client.send("⚠️ User does not exist".encode(ENCODING))
        return

    if sender_username not in ADMINS and target_user in ADMINS:
        client.send("⚠️ Cannot block admins".encode(ENCODING))
        return

    if sender_username == target_user:
        client.send("⚠️ Cannot block yourself".encode(ENCODING))
        return

    if sender_username not in blocked_users:
        blocked_users[sender_username] = set()

    blocked_users[sender_username].add(target_user)
    client.send(f"🚫 You have blocked {target_user}".encode(ENCODING))


def handle_unblock_command(client, sender_username, target_user):
    """Handle unblocking a user"""
    if target_user not in usernames:
        client.send("⚠️ User does not exist".encode(ENCODING))
        return

    if (
        sender_username not in blocked_users
        or target_user not in blocked_users[sender_username]
    ):
        client.send("⚠️ User is not blocked".encode(ENCODING))
        return

    blocked_users[sender_username].remove(target_user)
    client.send(f"✅ You have unblocked {target_user}".encode(ENCODING))


def handle_admin_command(client, sender_username, message):
    """Process admin commands"""
    if not message.startswith("/"):
        return

    parts = message[1:].split(maxsplit=1)
    if len(parts) != 2:
        client.send("⚠️ Usage: /command username".encode(ENCODING))
        return

    command, target_user = parts
    command = command.lower()

    # Handle block/unblock commands for all users
    if command in ["block", "unblock"]:
        if command == "block":
            handle_block_command(client, sender_username, target_user)
        else:
            handle_unblock_command(client, sender_username, target_user)
        return

    # Handle admin-only commands
    if sender_username not in ADMINS:
        client.send("🚫 Only admins can use this command!".encode(ENCODING))
        return

    if target_user not in usernames:
        client.send("⚠️ User does not exist".encode(ENCODING))
        return

    if target_user in ADMINS:
        client.send("⚠️ Cannot perform actions on other admins".encode(ENCODING))
        return

    if command == "kick":
        broadcast(f"👢 {target_user} was kicked by {sender_username}".encode(ENCODING))
        index = usernames.index(target_user)
        disconnect_client(clients[index], "YOU WERE KICKED BY AN ADMIN!")
        handle_client_disconnect(clients[index])

    elif command == "ban":
        broadcast(f"⛔ {target_user} was banned by {sender_username}".encode(ENCODING))
        BANNED_USERS.append(target_user)
        index = usernames.index(target_user)
        disconnect_client(clients[index], "YOU WERE BANNED BY AN ADMIN!")
        handle_client_disconnect(clients[index])

    elif command == "mute":
        MUTED_USERS.add(target_user)
        broadcast(f"🔇 {target_user} was muted by {sender_username}".encode(ENCODING))

    elif command == "unmute":
        if target_user in MUTED_USERS:
            MUTED_USERS.remove(target_user)
            broadcast(
                f"🔊 {target_user} was unmuted by {sender_username}".encode(ENCODING)
            )

    else:
        client.send(
            "❌ Invalid command! Available commands: /kick, /ban, /mute, /unmute, /block, /unblock".encode(
                ENCODING
            )
        )


def handle_client(client):
    """Handle individual client messages"""
    while True:
        try:
            # Use select to check if the socket is readable with a timeout
            readable, _, exceptional = select.select([client], [], [client], 1.0)

            if exceptional:
                raise socket.error("Socket exception")

            if readable:
                message = client.recv(2048).decode(ENCODING)
                if not message:
                    raise socket.error("Connection closed by client")

                sender_username = usernames[clients.index(client)]

                if message.startswith("/"):
                    handle_admin_command(client, sender_username, message)
                else:
                    if sender_username in MUTED_USERS:
                        client.send(
                            "🔇 You are muted and cannot send messages".encode(ENCODING)
                        )
                    else:
                        broadcast(message.encode(ENCODING), sender_username)

        except socket.error:
            handle_client_disconnect(client)
            break
        except Exception as e:
            log_message(f"Error handling client: {str(e)}")
            handle_client_disconnect(client)
            break


def authenticate_client(client):
    """Handle client authentication process"""
    try:
        client.send("USERNAME?".encode(ENCODING))
        username = client.recv(1024).decode(ENCODING)

        if not username:
            return False

        if username in BANNED_USERS:
            disconnect_client(client, "BANNED")
            return False

        if username in usernames:
            disconnect_client(client, "USERNAME TAKEN")
            return False

        if username in ADMINS:
            client.send("PASSWORD?".encode(ENCODING))
            password = client.recv(1024).decode(ENCODING)

            if password != ADMINS[username]:
                disconnect_client(client, "WRONG PASSWORD")
                return False

        usernames.append(username)
        clients.append(client)

        broadcast(f"✨ {username} joined the chat".encode(ENCODING))
        client.send("✅ Connected to server".encode(ENCODING))

        log_message(
            f"✅ User '{username}' {'(admin) ' if username in ADMINS else ''}connected"
        )
        broadcast(f"\t📊 Current users: {', '.join(usernames)}".encode(ENCODING))

        return True

    except Exception:
        disconnect_client(client)
        return False


def start_server():
    """Initialize and start the chat server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDRESS)
    server.listen()

    log_message(f"🚀 Server running on {HOST}:{PORT}")
    print("\n" + "=" * 50 + "\n")

    def handle_shutdown(signum, frame):
        log_message("💤 Server shutting down...")
        broadcast("SERVER IS SHUTTING DOWN...".encode(ENCODING))
        for client in clients[:]:
            disconnect_client(client)
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    while True:
        try:
            client, address = server.accept()
            log_message(f"📥 New connection from {address[0]}:{address[1]}")

            if authenticate_client(client):
                thread = threading.Thread(target=handle_client, args=(client,))
                thread.daemon = True
                thread.start()

        except Exception as e:
            log_message(f"❌ Error: {str(e)}")
            continue


if __name__ == "__main__":
    print("\n=== 💬 Chat Room Server ===\n")
    start_server()
