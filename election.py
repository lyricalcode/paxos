import threading
import socket

from server_util import sendTCP

# object for handling leader election for each node
class Election(object):
    def __init__(self, servers, sId):
        self.servers = servers
        self.id = sId

        self.currentLeader = None

        self.waitTime = 3.0
        self.waitTimer = None

        self.locked = False
        self.lockTime = 1.0
        self.lockTimer = None

        self.expirationTime = 7.0
        self.expirationTimer = None

    def isLeader(self):
        return self.currentLeader == self.id

    def getLeader(self):
        return self.currentLeader

    def startElection(self):
        # if max id, declare victory
        if self.id == max(self.servers.keys()):
            self._sendCoordinator()
            return
        # otherwise start election
        self._sendElection()
        # start timers
        self._startWaitTimer() # declare victory is no replies
        self._startExpirationTimer() # if no coordinator, start new election
    
    def handleElection(self, msg):
        sender = msg['sender']
        if sender < self.id:
            self._sendAnswer(sender)
            # if recently got a new leader, don't start new elections for lockout period
            if self.locked:
                return
            self.startElection()
        else:
            print('Error: Received election from higher server', file=sys.stderr)
    
    def handleAnswer(self, msg):
        sender = msg['sender']
        if sender < self.id:
            print('Error: Received answer from a lower server', file = sys.stderr)
        self._abortWaitTimer() # not the leader
        self._startExpirationTimer() # start new election eventually

    def handleCoordinator(self, msg):
        sender = msg['sender']
        if sender < self.id:
            self.startElection()
            return

        self.currentLeader = sender
        
        self._abortWaitTimer() # not leader, got new leader
        self._startLocked() # start lockout period
        self._startExpirationTimer() # restart expiration timer

    def _sendElection(self):
        msg = self._createBaseMsg('election')
        self._sendToHigher(msg)

    def _sendAnswer(self, target):
        msg = self._createBaseMsg('answer')
        sendTCP(self.servers[target], msg)

    def _sendCoordinator(self):
        msg = self._createBaseMsg('coordinator')
        self._sendToEveryone(msg)

    def _startWaitTimer(self):
        # if active wait, then no need to start one
        if self.waitTimer is not None and self.waitTimer.is_alive():
            return
        self.waitTimer = threading.Timer(self.waitTime, self._doneWaitTimer)
        self.waitTimer.start()

    def _abortWaitTimer(self):
        if self.waitTimer is not None and self.waitTimer.is_alive():
            self.waitTimer.cancel()

    def _doneWaitTimer(self):
        self._sendCoordinator()

    def _startLocked(self):
        if self.lockTimer is not None and self.lockTimer.is_alive():
            self.lockTimer.cancel()
        self.locked = True
        self.lockTimer = threading.Timer(self.lockTime, self._cancelLock)
        self.lockTimer.start()

    def _cancelLock(self):
        self.locked = False

    # cancels old expiration timer
    # starts a new timer after which an election will be started
    def _startExpirationTimer(self):
        if self.expirationTimer is not None and self.expirationTimer.is_alive():
            self.expirationTimer.cancel()
        self.expirationTimer = threading.Timer(self.expirationTime, self.startElection)
        self.expirationTimer.start()

    def _sendToEveryone(self, msg):
        for sId in self.servers:
            sendTCP(self.servers[sId], msg)

    def _sendToHigher(self, msg):
        for sId in self.servers:
            if sId > self.id:
                sendTCP(self.servers[sId], msg)

    # type: string
    def _createBaseMsg(self, type):
        msg = dict()
        msg['type'] = type
        msg['sender'] = self.id
        return msg