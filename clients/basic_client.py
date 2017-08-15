#!/usr/bin/python3

import sys
import json
import socket

MAX_MSG_SIZE = 1024

def prepare(msg):
    msg = json.dumps(msg)
    #print(msg)
    size = len(msg)
    if size > MAX_MSG_SIZE:
        print("Message size too big", file=sys.stderr)
    
    # make all msgs 1024 bytes
    msg = str.encode(msg)
    return msg

# address: (ip; str, port: int)
def send(address, msg):
    msg = prepare(msg)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, address)

if __name__ == '__main__':
    
    UDP_IP = '127.0.0.1'
    UDP_PORT = 9000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP,UDP_PORT))

    msg = dict()
    msg['type'] = 'request'
    msg['clientid'] = 1
    msg['reqid'] = 1
    msg['value'] = 'abc'
    msg['retip'] = UDP_IP
    msg['retport'] = UDP_PORT

    send(('127.0.0.1', 7001), msg)

    raw = sock.recv(MAX_MSG_SIZE)
    response = raw.decode()
    print(response)


