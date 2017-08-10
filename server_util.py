#!/usr/bin/python3

import json
import socket

# address (ip: str, port: int)
# msg should be a dictionary that will be converted to json, <= 1024 bytes
def send(address, msg):
    msg = json.dumps(msg)
    print(msg)
    size = len(msg)
    if size > 1024:
        print("Message size too big", file=sys.stderr)
    
    # make all msgs 1024 bytes
    msg = str.encode(msg.ljust(1024, '\0'))
    print(type(msg))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, address)

def recv(sock):
    data, addr = sock.recvfrom(1024)
    json_str = data.decode().strip('\0')
    msg = json.loads(json_str)
    return msg, addr