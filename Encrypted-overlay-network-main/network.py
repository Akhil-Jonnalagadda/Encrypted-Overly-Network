import socket
import threading
import json
import ssl

class Server:
    def __init__(self, host='192.168.6.228', port=33227):
        self.clients = {}
        self.host = host
        self.port = port
        # Create a default SSL context that enforces certificate validation
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # Load the server's certificate and private key
        # Note: Adjust these file paths if your files are located in a different directory
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        # Wrap the socket to include SSL encryption
        self.server_socket = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_side=True)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Secure server listening on {host}:{port}")

    def handle_client(self, client_socket, address):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                data = json.loads(data)
                if data['type'] == 'register':
                    # Include the client's name and the port it's listening on
                    self.clients[data['name']] = {"ip": address[0], "port": data['port']}
                    client_socket.send(json.dumps(self.clients).encode('utf-8'))
                elif data['type'] == 'list':
                    client_socket.send(json.dumps(self.clients).encode('utf-8'))
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def run(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Accepted secure connection from {address}")
            threading.Thread(target=self.handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    server = Server()
    server.run()
