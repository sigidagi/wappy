import ssl
import asyncio
import json
from datetime import datetime
import re
import sys
import logging
from configuration import wappy
from json.decoder import JSONDecodeError
from utils import randomize, Periodic
from bastard import Bastard

TCP_TIMEOUT = 20.0

module_logger = logging.getLogger(__name__)

networkRPC = {
    "jsonrpc": "2.0",
    "id": randomize("POST"),
    "method": "POST",
    "params": {
        "data": {
            "name": "WappyName",
            "meta": {
                "id": wappy.conf.backend.network_id,
                "type": "network",
                "version": "2.0"
            },
        },
        "url": "/network",
        "meta": {
            "send_time": datetime.utcnow().isoformat() + "Z"
        }
    }
}


# import pdb
async def bastard_connect(bastard, loop):
    global client_coro

    ctx = None
    if not wappy.conf.certs.skip:
        # pdb.set_trace()
        cafile = wappy.conf.path.certificates + wappy.conf.certs.ca_crt
        keyfile = wappy.conf.path.certificates + wappy.conf.certs.client_key
        certfile = wappy.conf.path.certificates + wappy.conf.certs.client_crt

        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                         cafile=cafile)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)

    while True:
        try:
            module_logger.info(' ****** Connecting to the backend server: '
                               + wappy.conf.backend.host
                               + ' port: '
                               + str(wappy.conf.backend.port) + ' ***********')

            client_coro = await loop.create_connection(
                lambda: bastard,
                wappy.conf.backend.host,
                wappy.conf.backend.port,
                ssl=ctx
            )
        except OSError as e:
            module_logger.warn(' Error: ' + str(e))
            module_logger.info(' Server ' + wappy.conf.backend.host
                                          + ' port: '
                                          + str(wappy.conf.backend.port)
                                          + ' is not UP. Retrying in 10 sec.')
            await asyncio.sleep(TCP_TIMEOUT)
        except Exception as e:
            module_logger.error(e)
            sys.exit(1)

        else:
            break


# TCP protocol
class WappClient(asyncio.Protocol):
    """
    Whenever WappClient send to device or to bastard it checks if response
    arrived, then next message will be send.
    """
    def __init__(self, loop):
        self.logger = logging.getLogger('wappclient')
        self.loop = loop
        self.network_callbacks = []
        self.deleted = []
        self.got = []
        self.uuid = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z', re.I) # noqa
        #
        self._pingback = Periodic(lambda: self.pingBackend())
        task_pingback = asyncio.ensure_future(self._pingback.start(120.0))

        def cb_pingback(future):
            self.logger.info(' Period send my network info!')
        task_pingback.add_done_callback(cb_pingback)

    def pingBackend(self):
        self.logger.info(" Resend network info to backend (aka ping)")
        self._bastard.append(networkRPC)

    """
        asyncio callback implementation
    """
    def connection_made(self, transport):
        """
        Method is called when connection with backend Server is established.
        Method is responsible for for sending all deserialized data
        from the lists to the server.
        """
        self.transport = transport
        self._bastard = Bastard(transport)

        self.logger.info(' Serialized Data was sent to Bastard: {!r}'
                         .format("----> done!"))

        # self._bastard.send()
        self._bastard.append(networkRPC)  # append and send

    def client_registration(self, uuid, callback):
        """
        """
        pass

    def data_send(self, jsonrpc):
        """
        Method will be called from client. it will set 'done_callback'
        function to call it once response from the bastard will arrive.
        """

        self.logger.info(" Received from client: {}".format(jsonrpc))

    """
        asyncion callback implementation
    """
    def data_received(self, data):
        """
        Method receives incomming reponses and commands from backend Server.
        Method is responsible for for separation of those two Server messages: response and command
        and update a list if needed. Client will request for update using 'CONTROL' message in 'data_send' method 
        """
        self.logger.info(" <---- Bastard DATA")
        try:
            msg = data.decode()
            jsonrpc = json.loads(msg)
        except JSONDecodeError as e:
            self.logger.warn("Received broken json: {}".format(e))

        self.logger.info(" <---- {}".format(jsonrpc))

    def connect_again(self):
        task = asyncio.ensure_future(bastard_connect(self, self.loop))

        def cb(future):
            self.logger.info(' --- Reconnection process finished! ---')
        task.add_done_callback(cb)

    """
        asyncio callback implementation.
    """
    def connection_lost(self, exc):
        self.logger.info('')
        self.logger.warn(' The server closed connection! \
                         Reconnect after {}'.format(TCP_TIMEOUT))
        self.loop.call_later(TCP_TIMEOUT, self.connect_again)
