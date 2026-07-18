import socket
import time
import webbrowser
from multiprocessing import Process

import toga
from toga.style import Pack

PAPER = "#123152"
INK = "#e9f0f7"
INK_DIM = "#93aec8"
ACCENT = "#ff7a33"
SUCCESS = "#6fcf97"

DEFAULT_PORT = 8000


def _run_server(host, port):
    from pfshare.server.app import create_app

    app = create_app()
    app.run(host=host, port=port, debug=False, use_reloader=False)


def _local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class Server:
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.process = None

    @property
    def running(self):
        return self.process is not None and self.process.is_alive()

    def start(self):
        self.process = Process(target=_run_server, args=(self.host, self.port), daemon=True)
        self.process.start()

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process.join(timeout=5)
            self.process = None


class PFShare(toga.App):
    def __init__(self):
        super().__init__()
        self.server = Server()
        self.status_label = None
        self.toggle_button = None
        self.address_input = None
        self.open_button = None
        self.log_view = None

    def _log(self, text):
        stamp = time.strftime("%H:%M:%S")
        self.log_view.value += f"[{stamp}] {text}\n"

    def _toggle_server(self, widget):
        if self.server.running:
            self.server.stop()
            self.status_label.text = "Stopped"
            self.status_label.style.color = INK_DIM
            self.address_input.value = ""
            self.open_button.enabled = False
            self.toggle_button.text = "Start Server"
            self._log("Server stopped.")
        else:
            self.server.start()
            address = f"http://{_local_ip()}:{self.server.port}"
            self.status_label.text = "Running"
            self.status_label.style.color = SUCCESS
            self.address_input.value = address
            self.open_button.enabled = True
            self.toggle_button.text = "Stop Server"
            self._log(f"Server started at {address}")

    def _open_in_browser(self, widget):
        if self.address_input.value:
            webbrowser.open(self.address_input.value)

    def on_exit(self):
        self.server.stop()
        return True

    def startup(self):
        title = toga.Label(
            "PFShare",
            style=Pack(font_size=24, font_weight="bold", color=INK, margin_bottom=4),
        )
        subtitle = toga.Label(
            "Share files with anyone on your network.",
            style=Pack(color=INK_DIM, margin_bottom=24),
        )

        self.status_label = toga.Label(
            "Stopped",
            style=Pack(color=INK_DIM, font_family="monospace", margin_right=12),
        )
        status_row = toga.Box(style=Pack(direction="row", align_items="center", margin_bottom=16))
        status_row.add(toga.Label("Status:", style=Pack(color=INK_DIM, margin_right=8)))
        status_row.add(self.status_label)

        self.toggle_button = toga.Button(
            "Start Server",
            on_press=self._toggle_server,
            style=Pack(
                background_color=ACCENT,
                color="#ffffff",
                margin_top=8,
                margin_bottom=8,
                margin_left=20,
                margin_right=20,
            ),
        )

        self.address_input = toga.TextInput(readonly=True, style=Pack(flex=1, font_family="monospace"))
        self.open_button = toga.Button(
            "Open in Browser",
            on_press=self._open_in_browser,
            style=Pack(margin_left=10),
        )
        self.open_button.enabled = False
        address_row = toga.Box(style=Pack(direction="row", margin_top=20, margin_bottom=10, align_items="center"))
        address_row.add(self.address_input)
        address_row.add(self.open_button)

        self.log_view = toga.MultilineTextInput(
            readonly=True,
            value="Ready. Press Start Server to begin sharing.\n",
            style=Pack(flex=1, font_family="monospace", font_size=11, margin_top=20),
        )

        home = toga.Box(style=Pack(direction="column", margin=30, background_color=PAPER, flex=1))
        home.add(title)
        home.add(subtitle)
        home.add(status_row)
        home.add(self.toggle_button)
        home.add(address_row)
        home.add(self.log_view)

        self.main_window = toga.MainWindow(title=self.formal_name, size=(640, 520))
        self.main_window.content = home
        self.main_window.show()


def main():
    return PFShare()
