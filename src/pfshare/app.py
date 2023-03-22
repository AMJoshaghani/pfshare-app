"""
Graphical User Interface for the PFShare project.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, VISIBLE, HIDDEN
from pfshare.server.app import app
from PyAccessPoint import pyaccesspoint as pap
from multiprocessing import Process
import random
import time
import netifaces as ni
# import webbrowser


class PFShare(toga.App):
    def __init__(self):
        super().__init__()
        self.ap = None
        self.serv = None

    def startup(self):
        def diag(start_or_stop):
            self.main_window.info_dialog(
                f"Service has been `{start_or_stop}`.",
                "Click again to toggle!"
            )

        def log(text, service):
            t = time.strftime('%H-%M-%S')
            service.value += f"[{t}]\t-\t{text}"
            logs.refresh()

        def start_server(widget, ap_enabled):
            if self.ap is None:  # TODO
                if ap_enabled != 0:
                    self.main_window.info_dialog(
                        'coming soon!',
                        'making access point is currently under construction...'
                    )
                    with_ap.value = not with_ap.value
                    # try:
                    #     self.ap = AccessPoint()
                    #     self.ap.start()
                    #     print(self.ap.stat())
                    #     server_log.value += "starting the access point.\n"
                    # except PermissionError:
                    #     with_ap.value = not with_ap.value
                    #     self.main_window.error_dialog(
                    #         'Permission Denied!',
                    #         'in case of running in AP enabled mode, root permission is required!\n'
                    #         'running without making AP...'
                    #     )
            else:
                pass
                # self.ap.stop()
                # log("stopping the access point.\n", log_text)

            if self.serv is None:
                ints = ni.interfaces()[-1]
                ip = ni.ifaddresses(ints)[ni.AF_INET][0]['addr']
                self.serv = Server()
                self.serv.serve()
                diag('started')
                # loc_link.on_press = lambda x: webbrowser.open('http://%s:5000' % ip)
                # loc_link.style.update(visibility=toga.style.pack.VISIBLE)
                # loc.style.update(visibility=toga.style.pack.VISIBLE)
                log("starting the server. "
                    "ask your friends to join you at %s:5000\n" % ip, log_text)
            else:
                self.serv.stop()
                self.serv = None
                diag('stopped')
                # loc_link.style.visibility = HIDDEN
                # loc.style.visibility = HIDDEN
                log("stopping the server.\n", log_text)

            if widget.text == "Stop!":
                widget.text = "Start the server!"
            else:
                widget.text = "Stop!"


        root = toga.OptionContainer()
        home = toga.Box(style=Pack(padding=100))
        logs = toga.Box(style=Pack())

        # ap_log = toga.MultilineTextInput(id='ap_log', value=self.ap_data, readonly=True, style=Pack(padding=50))
        # server_log = toga.MultilineTextInput(id='server_log', value=self.server_log, readonly=True)
        log_text = toga.MultilineTextInput(id='log', value='Application logs will be shown here.\n',
                                           readonly=True,
                                           style=Pack(padding=10, width=500))
        with_ap = toga.Switch(text="make Access Point", value=False)
        conn = toga.Button(text="Start the server!",
                           on_press=lambda x: start_server(x, with_ap.value))
        # loc = toga.Label(text="Sharing is possible through following address in your network:",  # TODO: TOGA
        #                  style=Pack(padding_top=40, visibility=HIDDEN))
        # loc_link = toga.Button(text='Open', style=Pack(padding=30, visibility=HIDDEN))

        # logs.content = [
        #     (server_log, 1),
        #     (ap_log, 1)
        # ]
        logs.add(log_text)

        root.style.update()
        # ap_log.style.update(font_family='monospace')
        # server_log.style.update(font_family='monospace')
        conn.style.update(padding_top=50)
        home.style.update(direction=COLUMN)

        root.add('Logs', logs)
        root.add('Home', home)
        home.add(with_ap)
        home.add(conn)
        # home.add(loc)
        # home.add(loc_link)

        root.current_tab = 'Home'

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = root
        self.main_window.show()


class AccessPoint:
    def __init__(self):
        self.ap_ID = random.randint(0, 100)
        self.pass_phrase = random.randint(100000, 999999)
        self.ip = '192.168.45.1'
        self.ap = pap.AccessPoint(wlan='wlp2s0',
                                  ssid='PFShare-%s' % str(self.ap_ID).zfill(2),
                                  password=self.ap_ID + self.pass_phrase)

    def start(self):
        self.ap.start()

    def stop(self):
        self.ap.stop()

    def stat(self):
        return self.ap.is_running()


class Server:
    def __init__(self):
        self.server = Process(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))

    def serve(self):
        self.server.start()

    def stop(self):
        self.server.terminate()


def main():
    return PFShare()
