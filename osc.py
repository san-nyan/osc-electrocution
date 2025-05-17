import requests
from pythonosc import dispatcher, osc_server, udp_client
import threading
from config import *
import fnmatch

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
    print("ow fuck")
    return response

class OSCForwarder:
    def __init__(self, listen_ip: str, listen_port: int, target_ip: str, target_ports: list[int]):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.target_clients = [udp_client.SimpleUDPClient(target_ip, port) for port in target_ports]

    def _forward_handler(self, address, *args):
        print(f"Received OSC message: {address} {args}")
        for client in self.target_clients:
            client.send_message(address, args)

    def start(self):
        disp = dispatcher.Dispatcher()
        disp.set_default_handler(self._forward_handler)

        server = osc_server.ThreadingOSCUDPServer((self.listen_ip, self.listen_port), disp)
        print(f"Listening on {self.listen_ip}:{self.listen_port}")
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        
if __name__ == "__main__":
    
    def match_shockosc(addr, args):
        return fnmatch.fnmatch(addr, "/avatar/parameters/ShockOsc*")

    def on_shockosc(addr, args):
        print(f"⚡ ShockOsc param: {addr} -> {args}")
        electrocution()
    
    forwarder = OSCForwarder(
        listen_ip="0.0.0.0",
        listen_port=9001,
        target_ip="127.0.0.1",
        target_ports=[9011]
    )
    forwarder.start()