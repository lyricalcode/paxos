#!/usr/bin/python3

class Proposal(object):
    def __init__(self, num, value, majority):
        self.propNum = num
        self.origValue = value
        self.majority = majority

        self.propAlive = True   
        self.value = value
        self.acceptedNum = None
        self.promises = set()
        self.promiseQuorumEstablished = False
        self.accepts = set()
        self.learned = False

    def getPropNum(self):
        return self.propNum

    # def setPropNum(self, num):
    #     self.propNum = num

    def getValue(self):
        return self.value

    # def setValue(self, val):
    #     self.value = val

    # def getAcceptedNum(self):
    #     return self.acceptedNum

    # def setAcceptedNum(self, num):
    #     self.acceptedNum = num

    def tryNumValue(self, anum, aval):
        # if there is an accepted value, set that as the new value
        if anum is not None:
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
        return self.promiseQuorumEstablished

    def addAccept(self, aId):
        self.accepts.add(aId)
        if len(self.accepts) >= self.majority:
            self.learned = True

    def isLearned(self):
        return self.learned

    def isAlive(self):
        return self.propAlive

    def killProposal(self):
        self.propAlive = False

    def resetProposal(self, num):
        self.propNum = num
        self.value = self.origValue
        self.acceptedNum = None
        self.promises = set()
        self.hasPromiseQuorum = False
        self.propAlive = True

if __name__ == '__main__':
    pass