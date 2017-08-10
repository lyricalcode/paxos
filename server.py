#!/usr/bin/python3

import sys
import os
import socket
import select
import queue
import pickle
import threading
import signal

from server_util import *
from base_actor import BaseActor
from proposer import Proposer
from acceptor import Acceptor
from learner import Learner

from election import Election

class Server(BaseActor):
    def __init__(self, servers, sId, stateFileName):
        BaseActor.__init__(self, servers, sId)
        self.stateFileName = stateFileName
        self.SERVER_IP = None
        self.UDP_PORT = None
        self.TCP_PORT = None
        self.udpSock = None
        self.tcpSock = None
        self.inputs = None

        self.currentRequests = set()
        self.requestQueue = queue.Queue()

        self.election = Election(servers, sId)

        self.recovery = True
        # self.recoveryLookahead = True
        self.inRecovery = set()
        # self.lookaheadIndex = None
        self.recoveryTimer = None

        self.proposer = None
        self.acceptor = None
        self.learner = None
        

    def _saveState(self):
        with open(self.stateFileName, 'wb') as sf:
            # pickle.dump((self.proposer, self.acceptor, self.learner), sf)
            pickle.dump(self.learner, sf)

    def _loadState(self):
        with open(self.stateFileName, 'rb') as sf:
            # self.proposer, self.acceptor, self.learner = pickle.loads(sf)
            self.learner = pickle.loads(sf)

    def _initActors(self):
        # if os.path.isfile(self.stateFileName):
        #     self._loadState()
        # else:
        self.proposer = Proposer(self.servers, self.id)
        self.acceptor = Acceptor(self.servers, self.id)
        self.learner = Learner(self.servers, self.id)     

    def _initNetworking(self):
        self.SERVER_IP, self.UDP_PORT, self.TCP_PORT = self.servers[self.id]
        print(self.SERVER_IP, self.UDP_PORT, self.TCP_PORT, self.id)

        self.udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSock.bind((self.SERVER_IP, self.UDP_PORT))

        self.tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSock.bind((self.SERVER_IP, self.TCP_PORT))
        self.tcpSock.listen(5)

        self.inputs = [ self.udpSock, self.tcpSock ]

    def init(self):
        self._initActors()
        self._initNetworking()

    def forwardToLeader(self, msg):
        leader = self.election.getLeader()
        if leader is None:
            self.election.startElection()
        else:
            send(self.servers[leader], msg)

    def handleRequest(self, msg):
        # is the leader, check is already complete, add to queue, propose when ready
        if self.election.isLeader():
            self.requestQueue.put(msg)
        else:
            self.forwardToLeader(msg)

    def handleLog(self, msg):
        if self.election.isLeader():
            log = sorted([ (k, v) for k, v in self.learner.learnedValues.items()])
            for entry in log:
                print(entry)
        else:
            self.forwardToLeader(msg)

    # def doLookahead(self):
    #     if not self.recoveryLookahead:
    #         self.lookaheadIndex = None
    #         return
    #     if not self.election.isLeader():
    #         return

    #     currentMaxIndex = self.learner.getMaxIndex()
    #     if currentMaxIndex is None:
    #         if self.lookaheadIndex is None:
    #             self.lookaheadIndex = self.learner.getBaseIndex()
    #             msg = self.createEmptyRequest(self.lookaheadIndex)
    #             self.proposer.newReqProposal(msg, self.lookaheadIndex)
    #     elif self.lookaheadIndex is None or self.lookaheadIndex <= currentMaxIndex:
    #         self.lookaheadIndex = currentMaxIndex + 1
    #         msg = self.createEmptyRequest(self.lookaheadIndex)
    #         self.proposer.newReqProposal(msg, self.lookaheadIndex)
    #     elif self.lookaheadIndex == currentMaxIndex + 1:
    #         # still at current lookahead
    #         return
    #     else:
    #         print('Error: Lookahead is too far ahead')
    
    def doRecovery(self):
        self.startRecoveryTimer()
        if not self.recovery: # and not self.recoveryLookahead:
            return
        # if not leader, stop with recovery
        if not self.election.isLeader():
            return
        
        missing = self.learner.getMissingValues()
        print('Missing: ', missing)
        print('inRecovery', self.inRecovery)
        # print('Lookahead', self.recoveryLookahead)
        # print('Index', self.lookaheadIndex)
        if len(missing) == 0:
            self.recovery = False
            self.inRecovery.clear()
            # # we're done with recovery, do lookahead if not done
            # self.doLookahead()
            return

        print('recovery')

        #if we need recovery, do lookahead later
        self.recoveryLookahead = True

        for index in missing:
            # already in recovery
            if index in self.inRecovery:
                continue
            self.inRecovery.add(index)
            # create dummy message to fill in gap
            msg = self.createEmptyRequest(index)
            self.proposer.newReqProposal(msg, index)

    def resetRecoveryState(self):
        self.recovery = True
    
    def startRecoveryTimer(self):
        if self.recoveryTimer is not None and self.recoveryTimer.is_alive():
            return

        self.recoveryTimer = threading.Timer(5.0, self.resetRecoveryState)
        self.recoveryTimer.start()

    def createEmptyRequest(self, index):
        msg = dict()
        msg['type'] = 'request'
        msg['clientid'] = self.id*-1 # negative server id will indicate server request
        msg['reqid'] = index # fake reqid
        msg['value'] = ""
        return msg
    
    def processRequest(self):
        if self.recovery or self.requestQueue.empty(): # or self.recoveryLookahead: 
            return
        msg = self.requestQueue.get()
        clientId = msg['clientid']
        clientReqId = msg['reqid']
        gReqId = getGlobalReqId(clientId, clientReqId)
        if self.learner.checkCompleted(gReqId):
            self.processRequest()
            return

        index = self.learner.getNextIndex()
        self.proposer.newReqProposal(msg, index)

    def handleAccepted(self, msg):
        resultLearner = self.learner.handleAccepted(msg)
        acceptedProposal = self.proposer.handleAccepted(msg)
        if resultLearner is False or acceptedProposal is None:
            return

        if resultLearner != acceptedProposal.isLearned():
            print('Error: Learner and Proposer disagree', acceptedProposal.isLearned(), file=sys.stderr)
            
        wasOverridden = acceptedProposal.isOverridden()
        origRetried = acceptedProposal.isOrigRetried()
        if wasOverridden and not origRetried:
            retryMsg = acceptedProposal.recreateOrigRequest()
            # if request was dummy, don't resubmit
            if retryMsg.get('clientid') < 0:
                acceptedProposal.setOrigRetried()
                return
            self.requestQueue.put(retryMsg)
            acceptedProposal.setOrigRetried()
        # elif not wasOverridden:
        #     self.recoveryLookahead = False
        
    def handleMsg(self, msg):
        if msg is None:
            return
        msgType = msg['type']
        if msgType == 'request':
            print('request')
            self.handleRequest(msg)
        elif msgType == 'log':
            print('log')
            self.handleLog(msg)
        elif msgType == 'prepare':
            print('prepare')
            self.acceptor.handlePrepare(msg)
        elif msgType == 'promise':
            print('promise')
            result = self.proposer.handlePromise(msg)
            # if result:
            #     self.recoveryLookahead = False
        elif msgType == 'accept':
            print('accept')
            self.acceptor.handleAccept(msg)
        elif msgType == 'accepted':
            print('accepted')
            self.handleAccepted(msg)
        else:
            print('msgType not recognized', file=sys.stderr)

    def handleElectionMsg(self, msg):
        if msg is None:
            return
        msgType = msg['type']
        if msgType == 'election':
            self.election.handleElection(msg)
        elif msgType == 'answer':
            self.election.handleAnswer(msg)
        elif msgType == 'coordinator':
            self.election.handleCoordinator(msg)
            self.proposer.setLeader(self.election.isLeader())
            print('Leader is:', self.election.getLeader())
        else:
            print('msgType not recognized', file=sys.stderr)

    def run(self):
        if self.election.getLeader() is None:
            self.election.startElection()
        while True:
            readable, writable, exceptional = select.select(self.inputs, [], [], 1)

            for s in readable:
                # tcpSock
                if s is self.tcpSock:
                    conn, addr = s.accept()
                    msg = recv(conn)
                    print('Received', msg)
                    conn.close()
                    self.handleElectionMsg(msg)
                # udpSock
                else:
                    msg = recv(s)
                    self.handleMsg(msg)
                    # self._saveState()

            self.doRecovery()
            self.processRequest()

        

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python server.py SERVER_LIST_FILE SERVER_ID STATE_FILE')
        sys.exit()

    serverList = sys.argv[1]
    myServerId = int(sys.argv[2])
    stateFile = sys.argv[3]

    print(serverList, myServerId, stateFile)

    servers = dict()
    with open(serverList, 'r') as f:
        for line in f:
            serverId, serverIp, udpPort, tcpPort = line.strip().split()
            serverId = int(serverId)
            udpPort = int(udpPort)
            tcpPort = int(tcpPort)
            servers[serverId] = (serverIp, udpPort, tcpPort)

    myServer = Server(servers, myServerId, stateFile)
    myServer.init()
    myServer.run()