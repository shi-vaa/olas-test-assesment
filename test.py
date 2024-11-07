import socket
import os
import time
import json
import pytest
import random

from w3 import W3
from dotenv import load_dotenv

load_dotenv()

server1_port = int(os.getenv("SERVER_1_PORT"))
server2_port = int(os.getenv("SERVER_2_PORT"))
host = "127.0.0.1"
from_address = os.getenv("FROM_ADDRESS")

alphabet = [
    "hello",
    "sun",
    "world",
    "space",
    "moon",
    "crypto",
    "sky",
    "ocean",
    "universe",
    "human",
]


def get_socket_connection(host, port):
    """Test the socket connection to the server."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        return s
    except socket.error as e:
        print(str(e))


def test_alphabet_behaviour():
    connection = get_socket_connection(host, server1_port)
    if not connection:
        pytest.fail(
            "Connection failed: Please run agent app, Integration tests will fail"
        )
    response = connection.recv(1024)
    connection.close()
    res_json = json.loads(response.decode("utf-8"))
    for word in res_json["words"]:
        assert word in alphabet


def test_balance_behaviour():
    w3 = W3()
    with open("app1.log", "r") as f:
        lines = f.readlines()
        total_lines = len(lines)
        found = 0
        if total_lines > 0:
            last_20_lines = lines[-(total_lines if total_lines < 20 else 20) :]
            for line in last_20_lines:
                if "Balance is:" in line:
                    line = line.split(":", 1)[1]
                    balance = float(line)
                    assert w3.get_balance(from_address) == balance
                    found = 1
                    f.close()
                    break
        if not found:
            pytest.fail("Could not find Balance keyword")


def test_hello_alphabet_behaviour():
    test_word = str(random.random())
    message = {
        "method": "Message",
        "type": "alphabet",
        "words": ["hello", test_word],
    }
    connection = get_socket_connection(host, server1_port)
    if not connection:
        pytest.fail(
            "Connection failed: Please run agent app, Integration tests will fail"
        )

    connection.send(json.dumps(message).encode("utf-8"))
    connection.close()
    time.sleep(3)  # wait until file stream gets updated

    with open("app1.log", "r") as f:
        msg = {}
        found = 0
        lines = f.readlines()
        total_lines = len(lines)
        if total_lines > 0:
            last_10_lines = lines[-(total_lines if total_lines < 10 else 10) :]
            for line in last_10_lines:
                if test_word in line and "Found hello:" in line:
                    msg = json.loads(line.split(":", 1)[1])
                    assert test_word in msg["words"]
                    found = 1
                    f.close()
                    break
        if not found:
            pytest.fail("Could not find logged in sent word")


def test_crypto_behaviour():
    with open("app1.log", "r") as f:
        test_word = str(random.random())
        message = {
            "method": "Message",
            "type": "alphabet",
            "words": ["crypto", test_word],
        }
        found = 0

        connection = get_socket_connection(host, server1_port)
        if not connection:
            pytest.fail(
                "Connection failed: Please run agent app, Integration tests will fail"
            )
        connection.sendall(json.dumps(message).encode("utf-8"))
        connection.close()
        time.sleep(3)  # wait until file stream gets updated

        lines = f.readlines()
        total_lines = len(lines)

        if total_lines > 0:
            last_10_lines = lines[-(total_lines if total_lines < 10 else 10) :]
            for line in last_10_lines:
                if test_word in line and "Found crypto initiating transfer:" in line:
                    found = 1
                    f.close()
                    break
        if not found:
            pytest.fail("Could not find logged in sent word")
