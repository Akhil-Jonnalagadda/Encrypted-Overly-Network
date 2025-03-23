import socket
import threading
import ssl
import time
import json
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Encrypted Client for Overlay Network')
    parser.add_argument('--network', type=str, help='Server host address', required=True)
    parser.add_argument('--name', type=str, help='Client name', required=True)
    args = parser.parse_args()
    return args.network, args.name

class Client:
    def __init__(self, name, server_host, server_port=33227):
        self.name = name
        self.server_host = server_host
        self.server_port = server_port
        
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations('server.crt')
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        self.socket = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=server_host)
        self.socket.connect((self.server_host, self.server_port))
        self.clients = {}
        self.start_listening()
        self.register()

    def start_listening(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('0.0.0.0', 0))
        listener.listen()
        self.listen_port = listener.getsockname()[1]
        print(f"Listening on port {self.listen_port}")
        threading.Thread(target=self.listen_for_messages, args=(listener,)).start()

    def listen_for_messages(self, listener):
        while True:
            conn, addr = listener.accept()
            conn = ssl.wrap_socket(conn, server_side=True, certfile='server.crt', keyfile='server.key', ssl_version=ssl.PROTOCOL_TLS)
            threading.Thread(target=self.handle_incoming_connection, args=(conn, addr)).start()

    def handle_incoming_connection(self, conn, addr):
        with conn:
            data = conn.recv(1024)
            if data:
                message = data.decode('utf-8')
                if message.startswith('PING'):
                    print(f"< Received PING from {addr[0]}, responding with PONG")
                    conn.sendall(b'PONG')

    def register(self):
        self.socket.send(json.dumps({'type': 'register', 'name': self.name, 'port': self.listen_port}).encode('utf-8'))
        response = json.loads(self.socket.recv(1024).decode('utf-8'))
        self.clients = response
        print(f"Registered with name {self.name}. Connected clients:")
        for client_name in self.clients.keys():
            if client_name != self.name:
                print(f"* {client_name}")

    def fetch_clients(self):
        self.socket.send(json.dumps({'type': 'list'}).encode('utf-8'))
        response = json.loads(self.socket.recv(1024).decode('utf-8'))
        self.clients = response
        print("- Found client(s):")
        for client_name in response.keys():
            if client_name != self.name:
                print(f"* {client_name}")

    def auto_ping(self):
        while True:
            time.sleep(10)  # Adjust timing as needed
            self.fetch_clients()  # Refresh the list of clients
            for client_name, info in self.clients.items():
                if client_name != self.name:
                    self.send_ping(info['ip'], info['port'], client_name)
            time.sleep(30)  # Adjust timing as needed

    def send_ping(self, target_ip, target_port, target_name):
        try:
            with socket.create_connection((target_ip, target_port)) as sock:
                sock = ssl.wrap_socket(sock, cert_reqs=ssl.CERT_NONE)
                print(f"> Sending PING to {target_name}")
                sock.sendall(b'PING')
                response = sock.recv(1024)
                print(f"< Received {response.decode()} from {target_name}")
        except Exception as e:
            print(f"Error sending PING to {target_name}: {e}")

    def run(self):
        threading.Thread(target=self.auto_ping).start()  # Combined fetching clients and auto-pinging into auto_ping

if __name__ == "__main__":
    network, name = parse_args()
    client = Client(name, network)
    client.run()

