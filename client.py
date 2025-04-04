import socket
import threading
import curses

HOST = "192.168.68.146"
PORT = 12342

def setup_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Default
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Own messages
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Incoming messages
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Idle messages

def receive_messages(client, chat_window):
    """ Continuously receive messages and update the chat window """
    chat_window.scrollok(True)
    while True:
        try:
            message = client.recv(1024).decode()
            if message:
                if message.startswith(">>>"):
                    color = curses.color_pair(1)  # White for idle
                else:
                    color = curses.color_pair(3)  # Blue for normal incoming
                chat_window.addstr(f"{message}\n", color)
                chat_window.refresh()
        except:
            break

def chat_client(stdscr):
    curses.echo()
    curses.curs_set(1)
    curses.nocbreak()
    stdscr.keypad(True)
    setup_colors()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    stdscr.addstr(0, 0, "Enter your name: ")
    stdscr.refresh()
    name = stdscr.getstr().decode().strip()
    client.send(name.encode())

    stdscr.addstr(1, 0, "Enter password: ")
    stdscr.refresh()
    password = stdscr.getstr().decode().strip()
    client.send(password.encode())

    stdscr.clear()
    stdscr.refresh()

    height, width = stdscr.getmaxyx()
    chat_window = curses.newwin(height - 2, width, 0, 0)
    input_box = curses.newwin(1, width, height - 1, 0)

    chat_window.scrollok(True)
    chat_window.refresh()

    threading.Thread(target=receive_messages, args=(client, chat_window), daemon=True).start()

    while True:
        input_box.clear()
        input_box.addstr(0, 0, "> ")
        input_box.refresh()

        message = input_box.getstr().decode().strip()

        if message.lower() == "-exit":
            client.send("-exit".encode())
            client.close()
            break

        elif message.lower() == "-clear":
            chat_window.clear()
            chat_window.refresh()
            continue

        elif message.lower() == "-idle":
            chat_window.clear()
            chat_window.refresh()
            client.send("-idle".encode())
            continue

        elif message.lower() == "-help":
            help_lines = [
                "\nAvailable Commands:",
                "-clear   → Clear chat window",
                "-rename <new_name> → Change username",
                "-exit    → Quit the chat",
                "-help    → Show this help message",
                "-tail    → Show last 50 messages"
            ]
            for line in help_lines:
                chat_window.addstr(f"{line}\n", curses.color_pair(1))
            chat_window.refresh()
            continue

        elif message.lower().startswith("-rename "):
            new_name = message.split(" ", 1)[1]
            if new_name:
                client.send(f"-rename {new_name}".encode())
                chat_window.addstr(f"Username changed to {new_name}\n", curses.color_pair(1))
                name = new_name
                chat_window.refresh()
            continue

        elif message.lower() == "-list":
            client.send("-list".encode())
            continue

        elif message.lower() == "-tail":
            client.send("-tail".encode())
            continue

        elif message.lower().startswith("-whisper "):
            parts = message.split(" ", 2)
            if len(parts) < 3:
                chat_window.addstr("Usage: -whisper <nickname> <message>\n", curses.color_pair(1))
                chat_window.refresh()
            else:
                target_nickname = parts[1]
                private_message = parts[2]
                whisper_message = f"-whisper {target_nickname} {private_message}"
                client.send(whisper_message.encode())
            continue

        client.send(message.encode())
        chat_window.addstr(f"You: {message}\n", curses.color_pair(2))  # Green for own
        chat_window.refresh()

curses.wrapper(chat_client)
