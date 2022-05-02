from threading import Lock, Thread
import socket
import time
import random


class Server:
    def __init__(self, port: int) -> None:
        self.port = port
        self.user_to_socket = {}
        self.lock = Lock()

    def register(self, client_socket: socket.socket, user_name: str) -> str:
        with self.lock:
            print("\n{0} registered!\n".format(user_name))
            self.user_to_socket[user_name] = client_socket
            client_socket.send("ack".encode())
            return user_name

    def get_user_list(self, client_socket: socket.socket) -> None:
        with self.lock:
            names = ','.join(self.user_to_socket.keys())
            client_socket.send(names.encode())

    def chat(self, from_user: str, to_user: str) -> None:
        with self.lock:
            # find user socket and then send message
            try:
                to_socket = self.user_to_socket[to_user]
                message = "{0} says hi\n".format(from_user)
                to_socket.send(message.encode())
            except Exception as ex:
                print("\nNo user by the name <{0}>. Error: {1}\n".format(to_user, ex))

    def handle_client(self, client_socket: socket.socket):
        current_user = None  # thread-local variable

        while True:
            data = client_socket.recv(4096).decode()  # get command
            command, args = data.split(":")

            if command == "register":
                current_user = self.register(client_socket, args)

            if command == "list":
                self.get_user_list(client_socket)

            if command == "chat":
                self.chat(current_user, args)

    def run_server(self):
        # networking stuff to setup the connection, that the can ignore
        socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_connection.bind(('', self.port))
        socket_connection.listen(5)

        # perpetually listen for new connections
        while True:
            client_socket, addr = socket_connection.accept()
            # spawn a thread to deal with a new client and immediately go back to
            # listening for new incoming connections
            Thread(target=self.handle_client, args=(client_socket, ), daemon=True).start()


class User:
    def __init__(self, name: str) -> None:
        self.name = name

    def receive_messages(self, server_socket: socket.socket) -> None:
        while True:
            response = server_socket.recv(4096).decode()
            print("\n{0} received: {1}\n".format(self.name, response))

    def start(self, server_host: str, server_port: int) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((server_host, server_port))

        # register and receive ack
        request = "register:{}".format(self.name).encode()
        server_socket.send(request)
        response = server_socket.recv(4096).decode()

        # wait for friends to join
        time.sleep(3.0)

        # get list of friends
        request = "list:friends".encode()
        server_socket.send(request)
        list_of_friends = server_socket.recv(4096).decode().split(',')

        print("\n{0} received: {1}\n".format(self.name, list_of_friends))

        # start listening for incoming messages
        # inside the thread we have a blocking operations
        Thread(target=self.receive_messages, args=(server_socket, ), daemon=True).start()

        while True:
            # randomly select a friend and send a message
            friend_id = random.randint(0, len(list_of_friends) - 1)
            friend_name = list_of_friends[friend_id]
            request = "chat:{0}".format(friend_name).encode()
            server_socket.send(request)
            time.sleep(random.randint(2, 6))


if __name__ == "__main__":
    server_port = random.randint(10000, 65000)
    server_host = "127.0.0.1"
    server = Server(server_port)
    # start server
    Thread(target=server.run_server, daemon=True).start()
    print("=============================")
    print("===== Start server app! =====\nPort: {0} Host:{1}".format(server_host, server_port))
    time.sleep(1.0)

    user_A = User("A")
    Thread(target=user_A.start, args=(server_host, server_port), daemon=True).start()

    user_B = User("B")
    Thread(target=user_B.start, args=(server_host, server_port), daemon=True).start()

    user_C = User("C")
    Thread(target=user_C.start, args=(server_host, server_port), daemon=True).start()

    time.sleep(30)