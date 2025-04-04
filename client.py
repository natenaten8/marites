import socket
import threading
import curses

HOST = "192.168.68.146"
PORT = 12342

# Define a function to set up colors in curses
def setup_colors():
    """ Set up color pairs for the chat window """
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default color pair
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green color pair
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Cyan color pair
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # Red color pair
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Yellow color pair

def receive_messages(client, chat_window, color_pair):
    """ Continuously receive messages and update the chat window """
    chat_window.scrollok(True)
    while True:
        try:
            message = client.recv(1024).decode()
            if message:
                chat_window.addstr(f"{message}\n", curses.color_pair(color_pair))
                chat_window.refresh()
        except:
            break

def chat_client(stdscr):
    """ Chat client UI using curses """
    curses.echo()  # Enable typed text visibility
    curses.curs_set(1)  # Make cursor visible
    curses.nocbreak()
    stdscr.keypad(True)

    # Set up colors
    setup_colors()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # Ask for username
    stdscr.addstr(0, 0, "Enter your name: ")
    stdscr.refresh()
    name = stdscr.getstr().decode().strip()
    client.send(name.encode())

    # Ask for password
    stdscr.addstr(1, 0, "Enter password: ")
    stdscr.refresh()
    password = stdscr.getstr().decode().strip()
    client.send(password.encode())

    # Set up UI
    stdscr.clear()
    stdscr.refresh()

    height, width = stdscr.getmaxyx()
    chat_window = curses.newwin(height - 2, width, 0, 0)  # Chat area
    input_box = curses.newwin(1, width, height - 1, 0)  # Input field

    chat_window.scrollok(True)
    chat_window.refresh()

    # Start receiving messages
    color_pair = 1  # Default color pair (white on black)
    threading.Thread(target=receive_messages, args=(client, chat_window, color_pair), daemon=True).start()

    while True:
        input_box.clear()
        input_box.addstr(0, 0, "> ")
        input_box.refresh()

        message = input_box.getstr().decode().strip()

        if message.lower() == "-exit":
            client.send("-exit".encode())  # Notify server
            client.close()
            break

        elif message.lower() == "-clear":
            chat_window.clear()  # Clear chat window
            chat_window.refresh()
            continue

        elif message.lower() == "-idle":
            chat_window.clear()  # Clear chat window
            chat_window.refresh()
            client.send("-idle".encode())
            continue

        elif message.lower() == "-help":
            chat_window.addstr("\nAvailable Commands:\n", curses.color_pair(color_pair))
            chat_window.addstr("-clear   → Clear chat window\n", curses.color_pair(color_pair))
            chat_window.addstr("-rename <new_name> → Change username\n", curses.color_pair(color_pair))
            chat_window.addstr("-exit    → Quit the chat\n", curses.color_pair(color_pair))
            chat_window.addstr("-help    → Show this help message\n", curses.color_pair(color_pair))
            chat_window.addstr("-tail    → Show last 50 messages\n", curses.color_pair(color_pair))
            chat_window.refresh()
            continue

        elif message.lower().startswith("-rename "):
            new_name = message.split(" ", 1)[1]
            if new_name:
                client.send(f"-rename {new_name}".encode())
                chat_window.addstr(f"Username changed to {new_name}\n", curses.color_pair(color_pair))
                name = new_name  # Update local username
                chat_window.refresh()
            continue

        elif message.lower() == "-list":
            client.send("-list".encode())  # Request list of active users
            continue

        elif message.lower() == "-tail":
            client.send("-tail".encode())  # Request last 50 messages
            continue

        elif message.lower().startswith("-whisper "):
            parts = message.split(" ", 2)
            if len(parts) < 3:
                chat_window.addstr("Usage: -whisper <nickname> <message>\n", curses.color_pair(color_pair))
                chat_window.refresh()
            else:
                target_nickname = parts[1]
                private_message = parts[2]
                whisper_message = f"-whisper {target_nickname} {private_message}"
                client.send(whisper_message.encode())
                continue

        elif message.lower().startswith("-color "):
            color_choice = message.split(" ", 1)[1].lower()
            if color_choice == "green":
                color_pair = 2
            elif color_choice == "cyan":
                color_pair = 3
            elif color_choice == "red":
                color_pair = 4
            elif color_choice == "yellow":
                color_pair = 5
            else:
                color_pair = 1  # Default color pair (white on black)
            chat_window.addstr(f"Color changed to {color_choice}\n", curses.color_pair(color_pair))
            chat_window.refresh()
            continue

        client.send(message.encode())
        chat_window.addstr(f"You: {message}\n", curses.color_pair(color_pair))  # Show own message
        chat_window.refresh()

curses.wrapper(chat_client)
