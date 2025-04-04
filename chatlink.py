import socket
import threading
import datetime
import time
import random

HOST = "0.0.0.0"
PORT = 12345

clients = []
nicknames = {}
idle_clients = {}  # Track idle state per client
LOG_FILE = "chat_log.txt"
PASSWORD = "water123"  # Set the server-side password here

def log_message(message):
    """ Logs messages to a file with timestamp and keeps only the last 50 lines """
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
    new_line = timestamp + message + "\n"

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    lines.append(new_line)
    lines = lines[-50:]  # Keep only the last 50 lines

    with open(LOG_FILE, "w") as f:
        f.writelines(lines)

def get_last_lines(filename, num_lines=50):
    """ Retrieves the last `num_lines` lines from a file """
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
            return "".join(lines[-num_lines:]) if lines else "No chat history available."
    except FileNotFoundError:
        return "Chat log file not found."

def fake_idle_stream(client):
    """ Continuously sends fake terminal output until toggled off """
    clear_screen = "\033c"  # ANSI code to clear terminal
    fake_lines = [
        ">>> Initializing module...",
        ">>> Loading neural net...",
        ">>> 0x1A2B3C4D: Packet received",
        ">>> Executing override...",
        ">>> Running diagnostics...",
        ">>> SYSTEM OK",
        ">>> Encrypting payload...",
        ">>> Connection secured.",
        ">>> Syncing with node...",
        ">>> Deploying script...",
        ">>> Injection complete.",
        ">>> Tracking user activity...",
        ">>> Memory dump: [#####     ] 60%",
    ]

    # Clear screen and enter idle mode
    client.send(clear_screen.encode())
    client.send("Entering idle mode. Type -idle again to exit.\n".encode())
    idle_clients[client] = True

    try:
        while idle_clients.get(client, False):
            line = random.choice(fake_lines)
            try:
                client.send((line + "\n").encode())
            except:
                break
            time.sleep(0.3)
    finally:
        client.send(clear_screen.encode())
        client.send("Exited idle mode.\n".encode())
        last_messages = get_last_lines(LOG_FILE, 20)
        client.send(f"While you were away:\n{last_messages}".encode())

def handle_client(client):
    """ Receives messages from a client and processes commands """
    try:
        client.send("Enter your nickname: ".encode())
        nickname = client.recv(1024).decode().strip()
        
        client.send("Enter password: ".encode())
        password = client.recv(1024).decode().strip()
        
        if password != PASSWORD:
            client.send("Incorrect password. Disconnecting...\n".encode())
            client.close()
            return

        nicknames[client] = nickname
        broadcast(f"{nickname} has joined the chat!", client)
        log_message(f"{nickname} has joined the chat!")

        while True:
            try:
                message = client.recv(1024).decode()
            except:
                break

            if not message:
                break

            if message == "-idle":
                client.send("\033c".encode())  # Clear screen first
                if idle_clients.get(client):
                    idle_clients[client] = False
                else:
                    threading.Thread(target=fake_idle_stream, args=(client,), daemon=True).start()
                continue

            if message.startswith("-rename "):
                new_name = message.split(" ", 1)[1]
                old_name = nicknames[client]
                nicknames[client] = new_name
                broadcast(f"{old_name} changed name to {new_name}", client)
                log_message(f"{old_name} changed name to {new_name}")
                continue

            if message == "-exit":
                break

            if message == "-tail":
                last_messages = get_last_lines(LOG_FILE, 50)
                client.send(f"Last 50 messages:\n{last_messages}".encode())
                continue

            if message == "-list":
                active_users = ", ".join(nicknames.values()) if nicknames else "No users connected."
                client.send(f"Active users: {active_users}".encode())
                continue

            if message.startswith("-whisper "):
                parts = message.split(" ", 2)
                if len(parts) < 3:
                    client.send("Usage: -whisper <nickname> <message>".encode())
                else:
                    target_nickname = parts[1]
                    private_message = parts[2]
                    target_client = None
                    for c, name in nicknames.items():
                        if name == target_nickname:
                            target_client = c
                            break
                    
                    if target_client:
                        target_client.send(f"Whisper from {nicknames[client]}: {private_message}".encode())
                    else:
                        client.send(f"User {target_nickname} not found.".encode())
                continue

            if message == "-help":
                help_text = """Available commands:
    -rename <new_nickname>: Change your nickname.
    -exit: Exit the chat.
    -tail: Get the last 50 messages from the chat log.
    -list: Show active users.
    -whisper <nickname> <message>: Send a private message.
    -idle: Toggle idle coding mode.
    -help: Show this help message."""
                client.send(help_text.encode())
                continue

            full_message = f"{nicknames[client]}: {message}"
            broadcast(full_message, client)
            log_message(full_message)
    
    except:
        pass
    finally:
        disconnect_client(client)

def broadcast(message, sender=None):
    """ Sends a message to all clients except the sender """
    log_message(message)
    for client in clients:
        if client != sender:
            try:
                client.send(message.encode())
            except:
                disconnect_client(client)

def disconnect_client(client):
    """ Removes a client and notifies others """
    if client in clients:
        nickname = nicknames.pop(client, "Someone")
        clients.remove(client)
        idle_clients.pop(client, None)
        client.close()
        broadcast(f"{nickname} has left the chat.")
        log_message(f"{nickname} has left the chat.")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"Server running on {HOST}:{PORT}")

while True:
    client, addr = server.accept()
    clients.append(client)
    print(f"New connection: {addr}")
    threading.Thread(target=handle_client, args=(client,), daemon=True).start()
