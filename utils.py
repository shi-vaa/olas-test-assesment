import socket

def is_port_active(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, port))            
        return True
    except ConnectionRefusedError:
        return False
    except socket.timeout:
        return False
    except socket.error as e:
        return False
