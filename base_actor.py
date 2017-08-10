from server_util import send
from math import floor

class BaseActor:
    def __init__(self, servers, sId):
        self.servers = servers
        self.id = sId
        self.majority = floor(len(servers)/2) + 1

    def _sendToAll(self, msg):
        for sId in self.servers:
            send(self.servers[sId], msg)

    # type: string
    def _createBaseMsg(self, index, type):
        msg = dict()
        msg['index'] = index
        msg['type'] = type
        msg['sender'] = self.id
        return msg