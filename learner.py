#!/usr/bin/python3

from base_actor import BaseActor
from server_util import send

class Learner(BaseActor):
    def __init__(self, servers, sId, index):
        BaseActor.__init__(self, servers, sId, index)
        self.acceptedValues = dict()
        self.learnedValue = None
        self.clientAddr = None
        self.clientPort = None
        self.clientNotified = False

    def registerRequest(self, imsg):
        if self.clientAddr is not None:
            # could do some still deciding thing here.
            self._notifyClient()
            return
        self.clientAddr = imsg['retaddr']
        self.clientPort = imsg['retport']

    # An acceptor has accepted a proposal
    def handleAccepted(self, imsg):
        # valid = imsg['valid']
        sender = imsg['sender']
        anum = imsg['anum']
        aval = imsg['aval']

        if self.acceptedValues.get((anum, aval)) is None:
            self.acceptedValues[(anum, aval)] = { sender }
        else:
            self.acceptedValues[(anum, aval)].add(sender)

        if len(self.acceptedValues[(anum, aval)]) >= self.majority:
            print('Learned', aval)
            self.learnedValue = aval
            self._notifyClient()

    def getLearnedValue(self):
        return self.learnedValue

    def _notifyClient(self):
        if self.clientAddr is None:
            return

        if self.learnedValue is None:
            self._sendPending()
        else:
            self._sendResult()

    def _sendPending(self):
        msg = dict()
        msg['type'] = 'result'
        msg['status'] = 'pending'
        msg['index'] = self.index
        
        send((self.clientAddr, self.clientPort), msg)

    def _sendResult(self):
        msg = dict()
        msg['type'] = 'result'
        msg['status'] = 'done'
        msg['index'] = self.index
        msg['val'] = self.learnedValue

        send((self.clientAddr, self.clientPort), msg)

if __name__ == '__main__':
    pass