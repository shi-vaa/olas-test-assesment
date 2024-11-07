import os
import time
import logging
import queue
import socket
import threading
import json

from json import JSONDecodeError

import utils
from agent import Agent


class JsonRpcServer:
    def __init__(
        self,
        port,
        external_agent_port,
        host="127.0.0.1",
    ):
        try:

            self.inbox_queue = queue.Queue()
            self.outbox_queue = queue.Queue()

            self.agent = Agent(self.inbox_queue, self.outbox_queue)

            self.host = host
            self.port = port
            self.external_agent_port = external_agent_port

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
                    response = self.agent.handle_request(message.decode())
                    client_socket.sendall(json.dumps(response).encode())
        except ConnectionResetError as e:
            logger.error("Connection reset by peer" + str(e))
        except socket.error as e:
            logger.error("Socket connection error" + str(e))
        finally:
            client_socket.close()

    def push_outbox_messages(self, client_socket):
        """
        Pushing all messages on outbox queue to connected
        """
        try:
            with client_socket:
                while True:
                    if not self.outbox_queue.empty():
                        item = self.outbox_queue.get()
                        self.outbox_queue.task_done()
                        client_socket.sendall(json.dumps(item).encode())
                        time.sleep(2)
        except socket.error as e:
            logger.error("connection lost" + str(e))
        finally:
            client_socket.close()

    def process_inbound_messages(self, connection):
        """ """
        with connection:
            try:
                while True:
                    message = connection.recv(1024)
                    self.inbox_queue.put(json.loads(message))
                    logger.info(f"Received: {message.decode('utf-8')}")
            except JSONDecodeError as e:
                logger.error("Invalid Json received" + str(e))
            except queue.Full:
                logger.error("Inbox Queue full" + str(e))
            except socket.error as e:
                logger.error("connection lost")
            except Exception as e:
                logger.error(
                    "Unknown exception while processing inbound messages" + str(e)
                )
            finally:
                connection.close()

    def connect_to_external_agent(self, port, max_retries=5):
        """
        Trying to establish a socket client connection with agent 2
        """

        time.sleep(5)  # wait until we start agent 2
        attempt = 0
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
                time.sleep(3)  # Wait before retrying
        logger.critical("Max retries reached. Could not connect.")
        return None

    def run(self):
        """
        With each socket connection, messages will pushed out
        and incoming messages will be processed in
        individual threads
        """
        self.agent.start()

        connection = self.connect_to_external_agent(self.external_agent_port, 5)
        if connection:
            connection_thread = threading.Thread(
                target=self.process_inbound_messages, args=(connection,)
            )
            connection_thread.start()

        while True:
            connected_socket, _ = self.server_socket.accept()

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

    server1_port = int(os.getenv("SERVER_1_PORT"))
    server2_port = int(os.getenv("SERVER_2_PORT"))

    port = (
        server2_port
        if utils.is_port_active(host="127.0.0.1", port=server1_port)
        else server1_port
    )

    external_agent_port = server2_port if port == server1_port else server1_port

    log_file_name = "app1.log" if port == server1_port else "app2.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file_name, mode="w"),
        ],
    )
    logger = logging.getLogger("App")

    server = JsonRpcServer(port=port, external_agent_port=external_agent_port)
    server.run()
