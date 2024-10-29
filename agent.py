import socket
import threading
import json
import os
import queue
import time
import logging

from dotenv import load_dotenv

from base_agent import BaseAgent
from behaviours import Behaviours
from handlers import Handlers
from w3 import W3

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

logger = logging.getLogger("App")

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
        logger.info("...Starting background behaviours & handlers...")
        self.behaviours.start()
        self.handlers.start()

    def stop(self):
        logger.info("...Stopping background behaviours & handlers...")
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
                logger.info(f"Received: {request.decode('utf-8')}")
                return {"result": "Message delivered to inbox"}
            else:
                return {"error": "Method not found"}
        except queue.Full as e:
            logger.error("inbox queue full" + str(e))
            return {"error": "unknown error"}
        except json.JSONDecodeError as e:
            logger.error("Json Decode error" + str(e))
            return {"error": "Invalid JSON"}
        except Exception as e:
            logger.error("Unknown Exception" + str(e))
            return {"error": str(e)}

    def register_handler(self, message_type, url):
        self.allowed_handlers[message_type] = url
        return {"result": "handler Registered"}

    def register_behaviour(self, name):
        if name in self.existing_behavious.keys():
            if self.existing_behavious[name]["is_active"]:
                return {"result": "Behaviour already active"}
            else:
                self.existing_behavious[name]["is_active"] = True
                return {"result": "Behaviour activated"}
        else:
            return {"result": "No such existing behaviour"}


class JsonRpcServer:
    def __init__(self, host="127.0.0.1", testing=False):
        try:

            self.agent = Agent()

            self.key = input("Please input agent number(1/2):") if not testing else 1
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
            logger.info(f"JSON-RPC server listening on {self.host}:{self.port}")
        except socket.error as e:
            logger.error("Exception while initializing socket" + str(e))
        except Exception as e:
            logger.error("unknown exception while initializing" + str(e))

    def handle_client(self, client_socket):
        """Function to handle communication with a connected client."""
        try:
            with client_socket:
                while True:
                    message = client_socket.recv(1024)
                    if not message:
                        break
                    response = self.agent.handle_request(message.decode())
                    client_socket.sendall(json.dumps(response).encode())
        except ConnectionResetError as e:
            logger.error("Connection reset by peer" + str(e))
        except socket.error as e:
            logger.error("Socket connection error" + str(e))

    def push_outbox_messages(self, client_socket):
        try:
            with client_socket:
                while True:
                    if not outbox_queue.empty():
                        item = outbox_queue.get()
                        outbox_queue.task_done()
                        logging.error("sending: " + json.dumps(item))
                        client_socket.sendall(json.dumps(item).encode())
                        time.sleep(2)
        except socket.error as e:
            logger.error("connection lost" + str(e))
        finally:
            client_socket.close()

    def process_inbound_messages(self, connection):
        with connection:
            try:
                while True:
                    message = connection.recv(1024)
                    inbox_queue.put(json.loads(message))
                    if not message:
                        break  # Break if no message (client disconnected)
                    logger.info(f"Received: {message.decode('utf-8')}")
            except queue.Full:
                logger.error("Inbox Queue full" + str(e))
            except socket.error as e:
                logger.error("connection lost")
            finally:
                connection.close()

    def connect_to_external_agent(self, max_retries=5):
        time.sleep(10)  # wait until we start agent 2
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
                logger.info(
                    f"Connected to {self.host}:{port} on attempt {attempt + 1}."
                )
                return sock
            except socket.error as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(5)  # Wait before retrying
        logger.critical("Max retries reached. Could not connect.")
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

            inbox_thread = threading.Thread(
                target=self.process_inbound_messages, args=(connected_socket,)
            )
            inbox_thread.start()


if __name__ == "__main__":
    server = JsonRpcServer()
    server.run()
