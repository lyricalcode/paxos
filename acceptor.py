#!/usr/bin/python3

import sys

from server_util import send
from base_actor import BaseActor

class Acceptor(BaseActor):
    def __init__(self, servers, sId):
        BaseActor.__init__(self, servers, sId)

        # {index: promiseNum}
        self.promises = dict()

        # {index: (propNum, propVal)}
        self.accepts = dict()

    def handlePrepare(self, imsg):
        propNum = imsg['propnum']
        senderId = imsg['sender']
        index = imsg['index']
        # promise not to accept any proposal with value < maxPropNum
        promiseNum = self.promises.get(index)
        omsg = self._createBaseMsg(index, 'promise')
        omsg['pnum'] = propNum
        if promiseNum is None or propNum > promiseNum:
            self.promises[index] = propNum
            omsg['valid'] = True
        else:
            omsg['valid'] = False
        
        omsg['promised'] = self.promises[index]
        
        # send promise back with any accepted value back
        if self.accepts.get(index) is None:
            omsg['anum'] = None
            omsg['aval'] = None
        else:
            anum, aval = self.accepts[index]
            omsg['anum'] = anum # accepted number
            omsg['aval'] = aval # accepted value
        send(self.servers[senderId], omsg)

    def handleAccept(self, imsg):
        pnum = imsg['pnum']
        pval = imsg['pval']
        msgSenderId = imsg['sender']
        index = imsg['index']

        if self.promises[index] > pnum:
            return

        self.accepts[index] = (pnum, pval)
        self.promises[index] = pnum

        omsg = self._createBaseMsg(index, 'accepted')
        # omsg['valid'] = True
        omsg['anum'] = pnum
        omsg['aval'] = pval

        self._sendToAll(omsg)

if __name__ == '__main__':
    pass