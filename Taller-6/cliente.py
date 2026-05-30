import socket
import sys
import pickle
import struct
import threading

SERVER_HOST = "localhost"
CHAT_SERVER_NAME = "server"

# Funciones auxiliares

def send(channel, *args):
    buffer = pickle.dumps(args)
    size = struct.pack("!I", len(buffer))

    channel.sendall(size)
    channel.sendall(buffer)

def receive(channel):
    size_data = channel.recv(4)

    if not size_data:
        return ""

    size = struct.unpack("!I", size_data)[0]
    buffer = b""

    while len(buffer) < size:
        data = channel.recv(size - len(buffer))

        if not data:
            break
        buffer += data
    if not buffer:
        return ""
    return pickle.loads(buffer)[0]

# Cliente

class ChatClient:

    def __init__(
            self,
            name,
            port,
            host=SERVER_HOST):
        
        self.name = name
        self.connected = False
        self.host = host
        self.port = port

        self.prompt = (
            f"[{name}@"
            f"{socket.gethostname()}] > "
        )
        try:
            self.sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            self.sock.connect(
                (host, self.port)
            )
            print(
                f"Conectado al servidor "
                f"en puerto {self.port}"
            )
            self.connected = True
            send(
                self.sock,
                "NAME: " + self.name
            )
            data = receive(self.sock)
            addr = data.split("CLIENT: ")[1]
            self.prompt = (
                f"[{self.name}@{addr}] > "
            )
        except socket.error as e:
            print(
                f"No fue posible conectar: {e}"
            )
            sys.exit(1)
            
    # Método para recibir mensajes del servidor
    def recibir_mensajes(self):

        while self.connected:
            try:
                data = receive(self.sock)
                if not data:
                    print("Cliente cerrando...")
                    self.connected = False
                    break
                print("\n" + data)
            except Exception:
                self.connected = False
                break

    # Método principal del cliente
    def run(self):
        hilo = threading.Thread(
            target=self.recibir_mensajes,
            daemon=True
        )
        hilo.start()

        try:

            while self.connected:
                data = input(self.prompt)
                if data:
                    send(self.sock, data)

        except KeyboardInterrupt:
            print("\nCliente interrumpido.")
        self.connected = False
        self.sock.close()