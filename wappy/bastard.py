"""

"""

import json
import logging
from utils import to_jsonrpc
import time


class Bastard:
    def __init__(self, transport):
        self.messages = []
        self.transport = transport
        self.bastard_ready = True
        self.logger = logging.getLogger(__name__)
        self.last_time = time.time()

    def send(self):
        self.logger.info(' Bastard is ready: {}'.format(self.bastard_ready))
        more_than_2min = bool((time.time() - self.last_time) // 120)
        if not self.bastard_ready and more_than_2min:
            self.logger.warn("Answer did not arrived more than 2 min. Send again.")
            self.bastard_ready = True

        if not self.bastard_ready:
            return
        if len(self.messages) == 0:
            self.logger.info(' Nothing to send - no messages')
            return

        self.last_time = time.time()
        self.bastard_ready = False
        # if qway.use_batch:

        if len(self.messages) == 1:
            msg = json.dumps(self.messages.pop())
        else:
            msg = json.dumps(self.messages)
            self.logger.info(' BATCH size: {}'.format(len(self.messages)))
            del self.messages[:]
        self.logger.info(' Sending to Bastard item(s) {!r}'.format(msg))
        self.transport.write(msg.encode())
        # else:
        # msg = self.messages.pop(0)
        # self.logger.info(' Sending to Bastard item {!r}'.format(msg))
        # self.transport.write(json.dumps(msg).encode())

    def append(self, item):
        if len(self.messages) > 1000:
            self.logger.warn(' Messages in buffer exceeds 1000, skipping this message')
        if type(item) is dict:
            # message = json.dumps(item)
            self.messages.append(item)
        elif type(item) is str:
            # assert
            assert(False)
            self.messages.append(item)
        else:
            # else object of type device, value or state
            message = to_jsonrpc(item)
            self.messages.append(message)
        self.send()

    def response(self, jsonrpc):
        # Response for client request
        if 'result' in jsonrpc:
            self.logger.info(' Bastard return result: {!r}, rpcid: {}'
                             .format(jsonrpc['result'], jsonrpc['id']))
        elif 'error' in jsonrpc:
            self.logger.error(' Bastard return error: {!r}, rpcid: {}'
                              .format(jsonrpc['error']['message'], jsonrpc['id']))

        self.bastard_ready = True
        # Response arrived - end a new message again if there is a queue
        self.send()
