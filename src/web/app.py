import os

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, disconnect, emit, send

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret!")
socketio = SocketIO(app)

# Dictionaries to store user nicknames, session IDs, and banned users
users = {}
sessions = {}
banned_users = set()


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/admin")
def admin():
    return render_template("admin.html", users=users, banned_users=banned_users)


@socketio.on("set_nickname")
def handle_set_nickname(data):
    if request.sid in banned_users:
        disconnect()
        return
    users[request.sid] = {"nickname": data["nickname"], "banned": False}
    sessions[request.sid] = request.namespace
    emit(
        "message",
        {"type": "text", "data": f"{data['nickname']} has joined the chat."},
        broadcast=True,
    )
    update_user_list()


@socketio.on("message")
def handle_message(message):
    if request.sid in banned_users or users[request.sid]["banned"]:
        disconnect()
        return

    nickname = users.get(request.sid, {}).get("nickname", "Anonymous")
    msg = {"type": message["type"], "data": message["data"]}

    if msg["type"] == "text":
        msg["data"] = f"{nickname}: {msg['data']}"
    elif msg["type"] == "image":
        msg["data"] = f"{nickname}: {message['data']}"

    print("Message: " + str(msg))
    send(msg, broadcast=True)


@socketio.on("admin_message")
def handle_admin_message(message):
    print(message)
    s = message["data"]
    msg = {"type": "text", "data": f"Admin: {s}"}
    send(msg, broadcast=True)


@app.route("/api/kick_user", methods=["POST"])
def api_kick_user():
    data = request.get_json()
    user_to_kick = data["sid"]
    if user_to_kick in users:
        sessions[user_to_kick].disconnect(user_to_kick)
        del users[user_to_kick]
        del sessions[user_to_kick]
        update_user_list()
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "User not found"})


@app.route("/api/ban_user", methods=["POST"])
def api_ban_user():
    data = request.get_json()
    user_to_ban = data["sid"]
    if user_to_ban in users:
        users[user_to_ban]["banned"] = True
        emit(
            "message",
            {
                "type": "text",
                "data": f"{users[user_to_ban]['nickname']} has been banned from the chat.",
            },
            broadcast=True,
        )
        update_user_list()
        sessions[user_to_ban].disconnect(user_to_ban)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "User not found"})


@app.route("/api/unban_user", methods=["POST"])
def api_unban_user():
    data = request.get_json()
    user_to_unban = data["sid"]
    if user_to_unban in users:
        users[user_to_unban]["banned"] = False
        emit(
            "message",
            {
                "type": "text",
                "data": f"{users[user_to_unban]['nickname']} has been unbanned from the chat.",
            },
            broadcast=True,
        )
        update_user_list()
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "User not found"})


@app.route("/api/user_list", methods=["GET"])
def api_user_list():
    user_list = {
        sid: {"nickname": users[sid]["nickname"], "banned": users[sid]["banned"]}
        for sid in users
    }
    return jsonify(user_list)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    nickname = users.pop(sid, {}).get("nickname", "Anonymous")
    emit(
        "message",
        {"type": "text", "data": f"{nickname} has left the chat."},
        broadcast=True,
    )
    update_user_list()


def update_user_list():
    user_list = {
        sid: {"nickname": users[sid]["nickname"], "banned": users[sid]["banned"]}
        for sid in users
    }
    emit("user_list", user_list, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True, host="127.0.0.1", port=int(os.getenv("PORT", 55555)))
