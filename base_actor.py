from server_util import send

class BaseActor:
    def __init__(self, servers, sId, index):
        self.servers = servers
        self.id = sId
        self.majority = len(servers)/2 + 1
        self.index = index

    def _sendToAll(self, msg):
        for sId in self.servers:
            send(self.servers[sId], msg)

    # type: string
    def _createBaseMsg(self, type):
        msg = dict()
        msg['type'] = type
        msg['sender'] = self.id
        msg['index'] = self.index
        return msg