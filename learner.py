#!/usr/bin/python3

from base_actor import BaseActor
from server_util import send

class Learner(BaseActor):
    def __init__(self, servers, sId):
        BaseActor.__init__(self, servers, sId)

        # {index: {(anum, aval): set of acceptors}}
        self.acceptedValues = dict()

        # {index: learnedValue}
        # learnedValue: {'id': gReqId, 'value': value }
        self.learnedValues = dict()

        # { gReqId: index } set of request id strings
        self.completedRequests = dict()

        # indices for which a reply has been sent
        self.replied = set()
        
        self.baseIndex = 0
        self.maxIndex = None

    # An acceptor has accepted a proposal
    def handleAccepted(self, imsg):
        # valid = imsg['valid']
        sender = imsg['sender']
        index = imsg['index']
        anum = imsg['anum']
        aval = imsg['aval']

        if self.acceptedValues.get(index) is None:
            self.acceptedValues[index] = dict()

        accepted = self.acceptedValues[index]

        avalkey = (aval.get('id'), aval.get('value'))
        if accepted.get((anum, avalkey)) is None:
            accepted[(anum, avalkey)] = { sender }
        else:
            accepted[(anum, avalkey)].add(sender)

        if len(accepted[(anum, avalkey)]) >= self.majority:
            #print('Learned', aval)
            self.learnedValues[index] = aval
            self.completedRequests[aval.get('id')] = index
            if self.maxIndex is None or index > self.maxIndex:
                self.maxIndex = index
            return True
        return False

    # reqId: clientId + reqId
    # returns index in log of completed request
    def getCompleted(self, reqId):
        return self.completedRequests.get(reqId)

    def getLearnedValue(self, index):
        return self.learnedValues.get(index)

    def getAllValues(self):
        return self.learnedValues

    def getMissingValues(self):
        print('MAX INDEX:', self.maxIndex)
        if self.maxIndex is None:
            return list()
        missing = list()
        for i in range(self.baseIndex, self.maxIndex):
            if i not in self.learnedValues:
                missing.append(i)
        return missing

    def getNextIndex(self):
        if self.maxIndex is None:
            self.maxIndex = self.baseIndex
        else:
            self.maxIndex += 1
        return self.maxIndex

    def getMaxIndex(self):
        return self.maxIndex
        
    def getBaseIndex(self):
        return self.baseIndex

    def exportDict(self):
        dump = dict()
        dump['learnedvalues'] = self.learnedValues
        #dump['completedrequests'] = self.completedRequests
        #dump['maxindex'] = self.maxIndex
        return dump

    def importDict(self, dump):
        self.learnedValues = dump['learnedvalues']
        #self.completedRequests = dump['completedrequests']
        #self.maxIndex = dump['maxindex']

        for val in self.learnedValues:
            self.completedRequests[self.learnedValues[val]['id']] = val
            if self.maxIndex is None or val > self.maxIndex:
                self.maxIndex = val

    def checkReply(self, index):
        return index in self.replied

    def addReply(self, index):
        self.replied.add(index)

if __name__ == '__main__':
    pass