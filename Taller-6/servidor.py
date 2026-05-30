import socket
import select
import sys
import signal
import pickle
import struct
import argparse
from xmlrpc import client
from cliente import ChatClient

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

# Servidor

class ChatServer:

    def __init__(self, port, backlog=5):

        self.clients = 0
        self.clientmap = {}
        self.outputs = []

        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        self.server.bind((SERVER_HOST, port))

        print(f"Servidor escuchando en puerto {port}")

        self.server.listen(backlog)

        signal.signal(
            signal.SIGINT,
            self.sighandler
        )
    def sighandler(self, signum, frame):

        print("Apagando servidor...")
        for output in self.outputs:
            output.close()
        self.server.close()
        sys.exit(0)

    def get_client_name(self, client):

        info = self.clientmap[client]
        host = info[0][0]
        name = info[1]

        return f"{name}@{host}"

    def run(self):

        inputs = [self.server]
        running = True
        
        while running:
            readable, writable, exceptional = select.select(
                inputs,
                self.outputs,
                []
            )
            for sock in readable:
                if sock == self.server:
                    client, address = self.server.accept()
                    print(
                        f"Nuevo cliente conectado desde {address}"
                    )
                    cname = receive(client).split("NAME: ")[1]
                    self.clients += 1
                    send(
                        client,
                        f"CLIENT: {address[0]}"
                    )
                    inputs.append(client)
                    self.clientmap[client] = (
                        address,
                        cname
                    )
                    msg = (
                        f"(Conectado: nuevo cliente "
                        f"{cname})"
                    )
                    for output in self.outputs:
                        send(output, msg)
                    self.outputs.append(client)
                else:
                    try:
                        data = receive(sock)
                        if data:
                            msg = (
                                f"\n"
                                f"[{self.get_client_name(sock)}]>> "
                                f"{data}"
                            )
                            for output in self.outputs:
                                if output != sock:
                                    send(output, msg)
                        else:
                            print(
                                "Cliente desconectado"
                            )
                            if sock in self.outputs:
                                self.outputs.remove(sock)
                            if sock in inputs:
                                inputs.remove(sock)
                            sock.close()

                    except socket.error:
                        if sock in self.outputs:
                            self.outputs.remove(sock)
                        if sock in inputs:
                            inputs.remove(sock)
                        sock.close()

# MAIN

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Chat usando select()"
    )
    parser.add_argument(
        "--name",
        required=True
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True
    )
    args = parser.parse_args()

    if args.name == CHAT_SERVER_NAME:

        server = ChatServer(args.port)
        server.run()
    else:
        client = ChatClient(
            name=args.name,
            port=args.port
        )
        client.run()
