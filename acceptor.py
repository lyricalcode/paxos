#!/usr/bin/python3

import sys
import json

from server_util import send
from base_actor import BaseActor

class Acceptor(BaseActor):
    def __init__(self, servers, sId, index):
        BaseActor.__init__(self, servers, sId, index)

        self.minPropNum = None
        self.acceptedPropNum = None
        self.acceptedValue = None

    def handlePrepare(self, imsg):
        msgPropNum = imsg['propnum']
        msgSenderId = imsg['sender']
        # promise not to accept any proposal with value < maxPropNum
        if self.minPropNum is None or msgPropNum > self.minPropNum:
            self.minPropNum = msgPropNum
        if msgPropNum <= self.minPropNum:
            omsg = self._createBaseMsg('promise')
            omsg['valid'] = False
            send(self.servers[msgSenderId], omsg)
            return
        
        # send promise back with any accepted value back
        omsg = self._createBaseMsg('promise')
        omsg['valid'] = True
        omsg['pnum'] = self.minPropNum # promise number
        omsg['anum'] = self.acceptedPropNum # accepted number
        omsg['aval'] = self.acceptedValue # accepted value
        send(self.servers[msgSenderId], omsg)

    def handleAccept(self, imsg):
        pnum = imsg['pnum']
        pval = imsg['pval']
        msgSenderId = imsg['sender']

        if self.minPropNum > pnum:
            # omsg = self._createBaseMsg('accepted')
            # omsg['valid'] = False
            # omsg['anum'] = pnum
            # omsg['aval'] = pval
            # send(self.servers[msgSenderId], omsg)
            return

        self.acceptedPropNum = pnum
        self.acceptedValue = pval

        omsg = self._createBaseMsg('accepted')
        # omsg['valid'] = True
        omsg['anum'] = pnum
        omsg['aval'] = pval

        self._sendToAll(omsg)
        


if __name__ == '__main__':
    pass