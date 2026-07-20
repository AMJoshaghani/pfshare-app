import os
import socket
import sys
import threading
import time
import webbrowser

import toga
from toga.style import Pack
from werkzeug.serving import make_server

TEXT_PRIMARY = "#1c2b3a"
TEXT_SECONDARY = "#6b7a89"
ACCENT = "#ff7a33"
SUCCESS = "#2f9e64"
DIVIDER = "#e2e6ea"

DEFAULT_PORT = 8000


def _android_share_root():
    try:
        from com.chaquo.python import Python

        context = Python.getPlatform().getApplication()
        external_dir = context.getExternalFilesDir(None)
        if external_dir is not None:
            return external_dir.getAbsolutePath()
        return context.getFilesDir().getAbsolutePath()
    except Exception:
        return None


def _configure_share_root():
    if os.environ.get("PFSHARE_ROOT"):
        return
    if hasattr(sys, "getandroidapilevel"):
        path = _android_share_root()
        if path:
            os.environ["PFSHARE_ROOT"] = path


def _android_context():
    from com.chaquo.python import Python

    return Python.getPlatform().getApplication()


def _start_android_service():
    try:
        from android.content import Intent
        from android.os import Build

        from pfshare.service import PFShareService

        context = _android_context()
        intent = Intent(context, PFShareService)
        if Build.VERSION.SDK_INT >= 26:
            context.startForegroundService(intent)
        else:
            context.startService(intent)
    except Exception:
        pass


def _stop_android_service():
    try:
        from android.content import Intent

        from pfshare.service import PFShareService

        context = _android_context()
        context.stopService(Intent(context, PFShareService))
    except Exception:
        pass


def _local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class ServerThread(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=True)
        _configure_share_root()
        from pfshare.server.app import create_app

        self.srv = make_server(host, port, create_app(), threaded=True)

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


class Server:
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.thread = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        self.thread = ServerThread(self.host, self.port)
        self.thread.start()
        if hasattr(sys, "getandroidapilevel"):
            _start_android_service()

    def stop(self):
        if self.thread is not None:
            self.thread.shutdown()
            self.thread.join(timeout=5)
            self.thread = None
        if hasattr(sys, "getandroidapilevel"):
            _stop_android_service()


class PFShare(toga.App):
    def __init__(self):
        super().__init__()
        self.server = Server()
        self.share_switch = None
        self.status_label = None
        self.address_input = None
        self.open_button = None
        self.log_view = None

    def _log(self, text):
        stamp = time.strftime("%H:%M:%S")
        self.log_view.value += f"[{stamp}] {text}\n"

    def _on_switch_change(self, widget):
        if widget.value:
            self.server.start()
            address = f"http://{_local_ip()}:{self.server.port}"
            self.status_label.text = f"Running at {address}"
            self.status_label.style.color = SUCCESS
            self.address_input.value = address
            self.open_button.enabled = True
            self._log(f"Server started at {address}")
        else:
            self.server.stop()
            self.status_label.text = "Not sharing"
            self.status_label.style.color = TEXT_SECONDARY
            self.address_input.value = ""
            self.open_button.enabled = False
            self._log("Server stopped.")

    def _open_in_browser(self, widget):
        if self.address_input.value:
            webbrowser.open(self.address_input.value)

    def on_exit(self):
        self.server.stop()
        return True

    def startup(self):
        title = toga.Label(
            "PFShare",
            style=Pack(font_size=22, font_weight="bold", color=TEXT_PRIMARY, margin_bottom=2),
        )
        subtitle = toga.Label(
            "Share files with anyone on your network.",
            style=Pack(color=TEXT_SECONDARY, font_size=13, margin_bottom=28),
        )

        self.share_switch = toga.Switch(
            "Share files",
            on_change=self._on_switch_change,
            style=Pack(font_size=15, color=TEXT_PRIMARY, margin_bottom=6),
        )

        self.status_label = toga.Label(
            "Not sharing",
            style=Pack(color=TEXT_SECONDARY, font_family="monospace", font_size=12, margin_bottom=20),
        )

        self.address_input = toga.TextInput(
            readonly=True,
            style=Pack(font_family="monospace", font_size=12, margin_bottom=8),
        )
        self.open_button = toga.Button(
            "Open in Browser",
            on_press=self._open_in_browser,
            style=Pack(
                background_color=ACCENT,
                color="#ffffff",
                font_size=13,
                margin_bottom=28,
            ),
        )
        self.open_button.enabled = False

        log_label = toga.Label(
            "Activity",
            style=Pack(color=TEXT_SECONDARY, font_size=12, margin_bottom=6),
        )
        self.log_view = toga.MultilineTextInput(
            readonly=True,
            value="Ready. Turn on Share files to begin.\n",
            style=Pack(flex=1, font_family="monospace", font_size=11),
        )

        divider = toga.Box(style=Pack(height=1, background_color=DIVIDER, margin_bottom=20))

        home = toga.Box(style=Pack(direction="column", margin=24, flex=1))
        home.add(title)
        home.add(subtitle)
        home.add(self.share_switch)
        home.add(self.status_label)
        home.add(self.address_input)
        home.add(self.open_button)
        home.add(divider)
        home.add(log_label)
        home.add(self.log_view)

        self.main_window = toga.MainWindow(title=self.formal_name, size=(420, 560))
        self.main_window.content = home
        self.main_window.show()


def main():
    return PFShare()
