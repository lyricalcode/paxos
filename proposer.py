#!/usr/bin/python3

import threading
from server_util import send
from proposal import Proposal
from base_actor import BaseActor

class Proposer(BaseActor):
    def __init__(self, servers, sId, index):
        BaseActor.__init__(self, servers, sId, index)
        # increment propNum by number of servers to prevent repeated propNum's
        self.propIncrement = len(servers)
        
        # proposal properties
        # base propNum is the ID due to uniqueness
        self.propNum = sId
        self.proposal = None
        
        self.resetTimer = None

    # value: string
    def newProposal(self, imsg):
        if self.proposal is not None:
            # already have a proposal
            return
        
        self.propNum += self.propIncrement
        self.proposal = Proposal(self.propNum, imsg['val'], self.majority)
        self._sendPrepare()

    def _sendPrepare(self):    
        #prepare
        #create msg
        omsg = self._createBaseMsg('prepare')
        omsg['propnum'] = self.proposal.getPropNum()

        self._sendToAll(omsg)

    def handlePromise(self, imsg):
        sender = imsg['sender']
        valid = imsg['valid']

        pnum = imsg['pnum']
        anum = imsg['anum']
        aval = imsg['aval']

        # response is old, ignore or already has a quorum
        if pnum != self.proposal.getPropNum() or not self.proposal.isAlive() \
            or self.proposal.hasPromiseQuorum() or self.proposal.isLearned():
            return

        # if not valid, proposal is doomed, abort
        if not valid:
            self.proposal.killProposal()
            # try again in a bit
            self._resubmitAfterTime()
            return
        
        # add sender to acceptor set
        self.proposal.addPromise(sender)
        self.proposal.tryNumValue(anum, aval)
        
        # check quorum
        if self.proposal.hasPromiseQuorum():
            # if has quorum and still nothing accepted, then the value will be original value
            omsg = self._createBaseMsg('accept')
            omsg['pnum'] = self.proposal.getPropNum()
            omsg['pval'] = self.proposal.getValue()
            self._sendToAll(omsg)

    def handleAccepted(self, imsg):
        # valid = imsg['valid']
        sender = imsg['sender']
        anum = imsg['anum']
        aval = imsg['aval']

        if self.proposal is None or anum != self.proposal.getPropNum():
            return

        if aval != self.proposal.getValue():
            print('Error: Different value for proposal number', file=sys.stderr)
            return

        self.proposal.addAccept(sender)

    def _resubmitAfterTime(self, seconds=5.0):
        if self.resetTimer is not None:
            self.resetTimer.cancel()
        self.resetTimer = threading.Timer(seconds, self._resubmit)
        self.resetTimer.start()
    
    def _resubmit(self):
        self.propNum += self.propIncrement
        self.proposal.reset(self.propNum)
        self._sendPrepare()


if __name__ == '__main__':
    pass