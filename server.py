#!/usr/bin/python3

import sys
import os
import socket
import json
import pickle
import threading

from server_util import *
from proposer import Proposer
from acceptor import Acceptor
from learner import Learner

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: python server.py UDP_IP UDP_PORT SERVER_LIST_FILE STATE_FILE')
        sys.exit()

    UDP_IP = sys.argv[1]
    UDP_PORT = int(sys.argv[2])
    serverFile = sys.argv[3]
    myServerId = None
    myStateFileName = sys.argv[4]

    servers = dict()
    with open(serverFile, 'r') as f:
        for line in f:
            serverId, ip, port = line.strip().split()
            serverId = int(serverId)
            port = int(port)
            if ip == UDP_IP and port == UDP_PORT:
                myServerId = serverId
            servers[serverId] = (ip, port)

    if myServerId is None:
        print('Error: IP or Port is incorrect', file=sys.stderr)
        sys.exit()

    if os.path.isfile(myStateFileName):
        with open(myStateFileName, 'rb') as sf:
            actorsForIndex = pickle.load(sf)
    else:
        actorsForIndex = dict()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP,UDP_PORT))

    print('Ready to listen on {} {}'.format(UDP_IP, UDP_PORT))
    while True:
        msg, addr = recv(sock)
        msgIndex = msg['index']
        if actorsForIndex.get(msgIndex) is None:
            paxosProposer = Proposer(servers, myServerId, msgIndex)
            paxosAcceptor = Acceptor(servers, myServerId, msgIndex)
            paxosLearner = Learner(servers, myServerId, msgIndex)
            actorsForIndex[msgIndex] = (paxosProposer, paxosAcceptor, paxosLearner)
        else:
            paxosProposer, paxosAcceptor, paxosLearner = actorsForIndex[msgIndex]

        msgType = msg['type']
        if msgType == 'set':
            print('set')
            paxosLearner.registerRequest(msg)
            paxosProposer.newProposal(msg)
        elif msgType == 'get':
            print('get')
            paxosLearner.registerRequest(msg)
        elif msgType == 'prepare':
            print('prepare')
            paxosAcceptor.handlePrepare(msg)
        elif msgType == 'promise':
            print('promise')
            paxosProposer.handlePromise(msg)
        elif msgType == 'accept':
            print('accept')
            paxosAcceptor.handleAccept(msg)
        elif msgType == 'accepted':
            print('accepted')
            paxosProposer.handleAccepted(msg)
            paxosLearner.handleAccepted(msg)
        else:
            print('msgType not recognized', file=sys.stderr)

        # picke state of everything for recovery from crash
        with open(myStateFileName, 'wb') as sf:
            pickle.dump(actorsForIndex, sf)


    