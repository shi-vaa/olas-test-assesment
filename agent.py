import socket
import threading
import json
import os
import queue
import time

from dotenv import load_dotenv

from base_agent import BaseAgent
from behaviours import Behaviours
from handlers import Handlers
from w3 import W3

load_dotenv()

# concurrent.futures
inbox_queue = queue.Queue()
outbox_queue = queue.Queue()


# thread safe stack with each instance for every client connection
class Agent(BaseAgent):
    def __init__(self):
        self.w3 = W3()

        self.handlers = Handlers(self.w3, inbox_queue)
        self.behaviours = Behaviours(self.w3, outbox_queue)

        self.stop_event = threading.Event()
        self.threads = []

    def start(self):
        print("...Starting background behaviours & handlers...")
        self.behaviours.start()
        self.handlers.start()

    def stop(self):
        print("...Stopping background behaviours & handlers...")
        self.behaviours.stop()  # Signal the behavious to stop

    def handle_request(self, request):
        try:
            req_data = json.loads(request)
            method = req_data.get("method")
            params = req_data.get("params", [])
            if method == "register_handler":
                return self.register_handler(*params)
            elif method == "register_behaviour":
                return self.register_behaviour(*params)
            if method == "Message":
                inbox_queue.put(req_data)
                return {"result": "Message delivered to inbox"}
            else:
                return {"error": "Method not found"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}
        except Exception as e:
            return {"error": str(e)}

    def register_handler(self, message_type, url):
        self.allowed_handlers[message_type] = url
        return {"result": "handler Registered"}

    def register_behaviour(self, name):
        if name in self.existing_behavious.keys():
            if self.existing_behavious[name]["is_active"]:
                return {"result": "Behaviour already active"}
            else:
                return {"result": "Behaviour activated"}
        else:
            return {"result": "No such existing behaviour"}


class JsonRpcServer:
    def __init__(self, host="127.0.0.1"):

        self.agent = Agent()

        self.key = 1
        # input("Please input agent number(1/2):")
        self.host = host
        self.port = (
            int(os.getenv("SERVER_1_PORT"))
            if int(self.key) == 1
            else int(os.getenv("SERVER_2_PORT"))
        )
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"JSON-RPC server listening on {self.host}:{self.port}")

    def handle_client(self, client_socket):
        """Function to handle communication with a connected client."""
        with client_socket:
            while True:
                # Receive data from the client
                message = client_socket.recv(1024)
                if not message:
                    break  # Break if no message (client disconnected)
                response = agent.handle_request(message)
                client_socket.sendall(json.dumps(response).encode())

    def push_outbox_messages(self, client_socket):
        try:
            with client_socket:
                while True:
                    if not outbox_queue.empty():
                        item = outbox_queue.get()  # Retrieve an item from the queue
                        outbox_queue.task_done()
                        client_socket.sendall(json.dumps(item).encode())
        except socket.error as e:
            print("connection lost")
        finally:
            client_socket.close()

    def process_inbound_messages(self, connection):
        with connection:
            try:
                while True:
                    # Receive data from the client
                    message = connection.recv(1024)
                    inbox_queue.put(message)
                    if not message:
                        break  # Break if no message (client disconnected)
                    # print(message)
                    print(f"Received: {message.decode('utf-8')}")
            except socket.error as e:
                print("connection lost")
            finally:
                connection.close()

    def connect_to_external_agent(self, max_retries=5):
        attempt = 0
        port = self.port = (
            int(os.getenv("SERVER_2_PORT"))
            if int(self.key) == 1
            else int(os.getenv("SERVER_1_PORT"))
        )
        while attempt < max_retries:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, port))
                print(f"Connected to {self.host}:{port} on attempt {attempt + 1}.")
                return sock
            except socket.error as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(5)  # Wait before retrying
        print("Max retries reached. Could not connect.")
        return None

    def run(self):
        self.agent.start()

        connection = self.connect_to_external_agent(7)
        if connection:
            connection_thread = threading.Thread(
                target=self.process_inbound_messages, args=(connection,)
            )
            connection_thread.start()

        while True:
            connected_socket, addr = self.server_socket.accept()

            # Create a new thread for each client
            client_thread = threading.Thread(
                target=self.handle_client, args=(connected_socket,)
            )
            client_thread.start()

            push_thread = threading.Thread(
                target=self.push_outbox_messages, args=(connected_socket,)
            )
            push_thread.start()


if __name__ == "__main__":
    server = JsonRpcServer()
    server.run()
