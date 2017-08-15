#!/usr/bin/python3
from server_util import splitGlobalReqId

class Proposal(object):
    def __init__(self, index, num, value, majority, retIp, retPort):
        self.index = index
        self.propNum = num
        # value: {'id': gReqId, 'value': value }
        self.origValue = value
        self.returnIP = retIp
        self.returnPort = retPort
        self.majority = majority
        self.origRetried = False

        self.propAlive = True
        self.valueOverridden = False   
        self.value = value
        # highest accepted num received from acceptors, determines which value to set prop to
        self.acceptedNum = None
        self.promises = set()
        self.promiseQuorumEstablished = False
        self.accepts = set()
        self.learned = False

        self.reuse = False

    def getPropNum(self):
        return self.propNum

    # increments should be based on propIncrement, which is the number of servers
    # this prevents duplicate prop numbers
    def incrementPropNum(self, increment):
        self.propNum += increment

    def getIndex(self):
        return self.index

    def getValue(self):
        return self.value

    def setValue(self, val):
        self.value = val

    def setOrigValue(self, val):
        self.origValue = val

    def tryNumValue(self, anum, aval):
        # if there is an accepted value, set that as the new value
        if anum is not None:
            self.valueOverridden = True
            if self.acceptedNum is None:
                self.acceptedNum = anum
                self.value = aval
            # if the received promise has a higher proposal number and value, set that value as the new value
            elif anum > self.acceptedNum:
                self.acceptedNum = anum
                self.value = aval

    def addPromise(self, aId):
        self.promises.add(aId)
        if len(self.promises) >= self.majority:
            self.promiseQuorumEstablished = True

    def hasPromiseQuorum(self):
        #print("Quorum", self.majority, len(self.promises), self.promiseQuorumEstablished)
        return self.promiseQuorumEstablished

    def addAccept(self, aId):
        self.accepts.add(aId)
        if len(self.accepts) >= self.majority:
            self.learned = True
            return True
        return False

    def isOverridden(self):
        return self.valueOverridden

    def isOrigRetried(self):
        return self.origRetried

    def setOrigRetried(self):
        self.origRetried = True

    def isLearned(self):
        return self.learned

    def isAlive(self):
        return self.propAlive

    # proposal is dead due to getting a higher propNum from acceptor
    def killProposal(self):
        self.propAlive = False
        self.reuse = False

    def markReuse(self):
        self.reuse = True

    def isReuse(self):
        return self.reuse

    # resets properties of the proposal
    def resetProposal(self, num):
        self.propNum = num
        self.value = self.origValue
        self.acceptedNum = None
        self.promises.clear()
        self.promiseQuorumEstablished = False
        self.accepts.clear()
        self.propAlive = True # should be okay due to updated propNum, promise and accept handling will not proceed until prop retried

    def recreateOrigRequest(self):
        msg = dict()
        msg['type'] = 'request'
        msg['clientid'], msg['reqid'] = splitGlobalReqId(self.origValue['id'])
        msg['value'] = self.origValue['value']
        return msg

    def getReturnInfo(self):
        return self.returnIP, self.returnPort

    # retInfo: (retIP, retPort)
    def setReturnInfo(self, retInfo):
        self.returnIP, self.returnPort = retInfo

if __name__ == '__main__':
    pass