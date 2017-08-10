#!/usr/bin/python3

import json
import socket
import sys

MSG_SIZE = 1024

# int, int
def getGlobalReqId(clientId, clientReqId):
    return str(clientId) + "_" + str(clientReqId)

def splitGlobalReqId(gReqId):
    clientId, clientReqId = gReqId.split('_')
    return int(clientId), int(clientReqId)

def prepare(msg):
    msg = json.dumps(msg)
    #print(msg)
    size = len(msg)
    if size > 1024:
        print("Message size too big", file=sys.stderr)
    
    # make all msgs 1024 bytes
    msg = str.encode(msg.ljust(MSG_SIZE, '\0'))
    return msg

def extractUDPPair(address):
    ip, udp, tcp = address
    return (ip, udp)

def extractTCPPair(address):
    ip, udp, tcp = address
    return (ip, tcp)

# address (ip: str, udpport: int, tcpport: int)
# msg should be a dictionary that will be converted to json, <= 1024 bytes
def send(address, msg):
    msg = prepare(msg)
    address = extractUDPPair(address)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, address)

def sendTCP(address, msg):
    msg = prepare(msg)
    address = extractTCPPair(address)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(address)
        sock.send(msg)
        sock.close()
    except socket.error:
        return

def recv(sock):
    data = sock.recv(MSG_SIZE)
    json_str = data.decode().strip('\0')
    try:
        msg = json.loads(json_str)
        return msg
    except json.decoder.JSONDecodeError:
        return