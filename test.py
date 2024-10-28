

import socket
import pytest
import threading
import time

from agent import Agent, JsonRpcServer


@pytest.fixture(scope="module")
def socket_server():
    """Fixture to start the socket server in a separate thread."""
    server = JsonRpcServer()
    server_thread = threading.Thread(server.run())
    server_thread.daemon = True 
    server_thread.start()
    time.sleep(1)
    yield

def test_socket_connection(socket_server):
    """Test the socket connection to the server."""
    host = '127.0.0.1'
    port = 4001

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        message = b'Hello, Server!'
        s.sendall(message)
        data = s.recv(1024)

    assert data == message  # Check if the server echoed back the correct message
