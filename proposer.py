#!/usr/bin/python3

import sys
import threading
from server_util import send, getGlobalReqId, splitGlobalReqId
from proposal import Proposal
from base_actor import BaseActor

class Proposer(BaseActor):
    def __init__(self, servers, sId):
        BaseActor.__init__(self, servers, sId)
        # increment propNum by number of servers to prevent repeated propNum's
        self.propIncrement = len(servers)
        
        # proposal properties
        # base propNum is the ID due to uniqueness
        self.basePropNum = sId

        # dictionary: {index: proposal}
        self.proposals = dict()
        self.propNums = dict()
        
        self.resetTimers = dict()

        self.isLeader = False

    def newReqProposal(self, imsg, index):
        clientId = imsg['clientid'] #int
        clientReqId = imsg['reqid'] #int
        value = imsg['value'] #str

        clientRetIP = imsg.get('retip') #str
        clientRetPort = imsg.get('retport') #int
        
        if not isinstance(clientId, int) or \
            not isinstance(clientReqId, int) or \
            not isinstance(value, (str, int)):
            # request is invalid
            print('REQUEST INVALID', file=sys.stderr)
            return
        
        gReqId = getGlobalReqId(clientId, clientReqId)

        logValue = {'id': gReqId, 'value': value }

        # special case from lookahead, already have promises, directly accept
        currentProposal = self.proposals.get(index)
        if currentProposal is not None and currentProposal.isReuse():
            currentProposal = self.proposals.get(index)
            currentProposal.setValue(logValue)
            currentProposal.setOrigValue(logValue)
            currentProposal.setReturnInfo((clientRetIP, clientRetPort))
            self._sendAccept(index)
            return
        elif currentProposal is not None:
            print('Error: Submitting a new proposal for index failed')
            return

        self.propNums[index] = self.basePropNum
        self.proposals[index] = Proposal(index, self.propNums[index], logValue, self.majority, clientRetIP, clientRetPort)
        self._sendPrepare(index)

    def _sendPrepare(self, index):
        if not self.isLeader:
            self._cancelRetry(index)
            return    
        #prepare
        #create msg
        omsg = self._createBaseMsg(index, 'prepare')
        omsg['propnum'] = self.proposals[index].getPropNum()

        self._sendToAll(omsg)
        self._retryAfterTime(index)

    # return True if found empty slot during recovery
    def handlePromise(self, imsg):
        sender = imsg['sender']
        valid = imsg['valid']
        index = imsg['index']

        pnum = imsg['pnum']
        anum = imsg.get('anum')
        aval = imsg.get('aval')
        promised = imsg.get('promised')

        currentProposal = self.proposals.get(index)
        # response is old, ignore or already has a quorum
        if currentProposal is None or \
            pnum != currentProposal.getPropNum() or \
            not currentProposal.isAlive() \
            or currentProposal.hasPromiseQuorum() or \
            currentProposal.isLearned():
            return False

        # if not valid, proposal is doomed, abort
        if not valid:
            currentProposal.killProposal()

            # need higher propNum
            diff = promised % self.propIncrement
            newPropNum = promised - diff

            print('RESET, newPropNum: ', newPropNum)
            currentProposal.resetProposal(newPropNum)
            # try again in a bit/will be auto retried later
            self._retryAfterTime(index)
            return False

        # add sender to acceptor set
        self.proposals[index].addPromise(sender)
        self.proposals[index].tryNumValue(anum, aval)
        
        # check quorum
        if self.proposals[index].hasPromiseQuorum():
            if not currentProposal.isOverridden():
                if self.isRecoveryProp(index):
                    #found the head of the log
                    currentProposal.markReuse()
                    # don't retry after interval
                    self._cancelRetry(index)
                    return True
            # if has quorum and still nothing accepted, then the value will be original value
            self._sendAccept(index)
        return False

    def isRecoveryProp(self, index):
        currentProposal = self.proposals.get(index)
        val = currentProposal.getValue()
        gId = val.get('id')
        cId, rId = splitGlobalReqId(gId)
        return cId < 0

    def _sendAccept(self, index):
        currentProposal = self.proposals.get(index)
        omsg = self._createBaseMsg(index, 'accept')
        omsg['pnum'] = currentProposal.getPropNum()
        omsg['pval'] = currentProposal.getValue()
        self._sendToAll(omsg)
        self._retryAfterTime(index)

    def handleAccepted(self, imsg):
        sender = imsg['sender']
        anum = imsg['anum']
        aval = imsg['aval']
        index = imsg['index']

        currentProposal = self.proposals.get(index)
        # prevents reaction to accepted proposals from other proposers
        if currentProposal is None or anum != currentProposal.getPropNum():
            return

        if aval != currentProposal.getValue():
            print('Error: Different value for proposal number', aval, currentProposal.getValue(), file=sys.stderr)
            return

        result = currentProposal.addAccept(sender)

        if result:
            self._cancelRetry(index)

        return currentProposal

    def checkPropStatus(self, index):
        currentProposal = self.proposals.get(index)
        if currentProposal is None:
            print('Error: Checking status of invalid index')
        return currentProposal.isOverridden()

    # retry logic
    # retry after interval or 
    def _retryAfterTime(self, index, seconds=4.0):
        self._cancelRetry(index)
        if not self.isLeader:
            return
        self.resetTimers[index] = threading.Timer(seconds, self._retryProposal, [ index ])
        self.resetTimers[index].start()

    def _cancelRetry(self, index):
        retryTimer = self.resetTimers.get(index)
        if retryTimer is not None and retryTimer.is_alive():
            retryTimer.cancel()

    def _retryProposal(self, index):
        if self.proposals[index].isLearned() or not self.isLeader:
            return

        # left too long, will eventually crash/overflow
        # could retry some sort of backoff in retry interval
        self.proposals[index].incrementPropNum(self.propIncrement)

        # proposal is being retried as is due to lack of responses or 
        self._sendPrepare(index)

    def setLeader(self, status):
        self.isLeader = status

if __name__ == '__main__':
    pass