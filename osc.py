import requests
from pythonosc import dispatcher, osc_server, udp_client
import threading
import time
from config import *
last_shock_time = 0
def electrocution() -> requests.Response:
    url = "https://api.openshock.app/2/shockers/control"
    headers = {
        "Content-Type": "application/json",
        "OpenShockToken": api_key,
    }
    payload = {
        "shocks": [
            {
                "id": device_id,
                "type": "Shock",
                "intensity": intensity,
                "duration": duration,
                "exclusive": True,
            }
        ],
        "customName": None,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("⚡ ow fuck")
    return response

class OSCForwarder:
    def __init__(self, listen_ip: str, listen_port: int, target_ip: str, target_ports: list[int]):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.target_clients = [
            udp_client.SimpleUDPClient(target_ip, port)
            for port in target_ports
        ]
        self.custom_handlers: list[tuple[callable, callable]] = []

    def add_handler(self, match_fn: callable, handler_fn: callable):
        self.custom_handlers.append((match_fn, handler_fn))

    def _forward_handler(self, address: str, *args):
        for match_fn, handler_fn in self.custom_handlers:
            if match_fn(address, args):
                handler_fn(address, args)
        for client in self.target_clients:
            client.send_message(address, args)

    def start(self):
        disp = dispatcher.Dispatcher()
        disp.set_default_handler(self._forward_handler)
        server = osc_server.ThreadingOSCUDPServer(
            (self.listen_ip, self.listen_port), disp
        )
        print(f"Listening on {self.listen_ip}:{self.listen_port}")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

if __name__ == "__main__":
    def match_shockosc(addr, args):
        if not addr.startswith("/avatar/parameters/ShockOsc"):
            return False
        if len(args) != 1:
            return False
        value = args[0]
        return value in (0, 1, 0.0, 1.0)

    def on_shockosc(addr, args):
        global last_shock_time
        now = time.time()
        if now - last_shock_time < cooldown_seconds:
            print(f"⏳ Cooldown active: {round(cooldown_seconds - (now - last_shock_time), 2)}s remaining")
            return
        print(f"⚡ ShockOsc param matched: {addr} -> {args}")
        last_shock_time = now
        electrocution()

    forwarder = OSCForwarder(
        listen_ip="127.0.0.1",
        listen_port=listen_port,
        target_ip="127.0.0.1",
        target_ports=target_ports
    )
    forwarder.add_handler(match_shockosc, on_shockosc)
    forwarder.start()

    threading.Event().wait()