import socket
import os
import time
import json

from w3 import W3
from dotenv import load_dotenv

load_dotenv

server1_port = 4001
server2_port = 4002
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

    i = 10  # testing for 10 responses

    while i > 0:
        response = connection.recv(1024)
        res_json = json.loads(response.decode("utf-8"))
        for word in res_json["words"]:
            assert word in alphabet
        i = i - 1


def test_balance_behaviour():
    w3 = W3()
    with open("app1.log", "r") as file:
        index = 1

        file.seek(0, 2)

        while index <= 3:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            if "Balance is:" in line:
                line = line.split(":", 1)[1]
                line = line.split("LINK")[0]
                balance = float(line)
                assert w3.get_balance(from_address) == balance
                index += 1


def test_hello_alphabet_behaviour():
    with open("app1.log", "r") as f:
        connection = get_socket_connection(host, server1_port)
        key = 1
        while key <= 10:
            test_word = "test" + str(key)
            message = {
                "method": "Message",
                "type": "alphabet",
                "words": ["hello", test_word],
            }
            connection.sendall(json.dumps(message).encode("utf-8"))
            key += 1
            f.seek(0, 2)
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            print(line, end="")
            if "Found hello:" in line:
                msg = json.loads(line.split(":", 1)[1])
                assert test_word in msg["words"]
            
            
            

        connection.close()


def test_crypto_behaviour():
    with open("app1.log", "r") as f:
        key = 1
        waiting_lines = 1
        while waiting_lines < 20 and key <= 2:
            test_word = "test" + str(key)
            message = {
                "method": "Message",
                "type": "alphabet",
                "words": ["crypto", test_word],
            }
            connection = get_socket_connection(host, server1_port)
            connection.sendall(json.dumps(message).encode("utf-8"))
            connection.close()
            f.seek(0, 2)
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            print(line, end="")
            msg = {}
            if "Found crypto initiating transfer:" in line:
                msg = json.loads(line.split(":", 1)[1])
                assert test_word in msg["words"]
            else:
                waiting_lines += 1  # waits till 20 responses
