""" """

import random
import asyncio
import logging
from contextlib import suppress
from datetime import datetime


class dotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def randomize(optional_str):
    num = random.randint(3000, 5999)
    if optional_str:
        return optional_str + str(num)
    else:
        return str(num)


def to_jsonrpc(network_id, iobject, method='POST'):
    if not iobject.location:
        print(iobject)
        assert(False)

    # if method POST - from location remove UUID
    if method == 'POST':
        idx = iobject.location.rfind('/')
        url = iobject.location[:idx]
    else:
        url = iobject.location

    # remove clients network UUID add qway network UUID
    url_list = url.split('/')

    idx = url_list.index('network')
    if len(url_list) > idx+1:
        url_list[idx+1] = network_id

    url = "/" + '/'.join(url_list)
    jsonrpc = {
        "jsonrpc": "2.0",
        "id": randomize("POST"),
        "method": method,
        "params": {
            "data": iobject.data,
            "url": url,
            "meta": {
                "send_time": datetime.utcnow().isoformat() + "Z"
            }
        }
    }
    return jsonrpc


class Periodic:
    def __init__(self, func, repeat=True):
        self.func = func
        self.repeat = repeat
        self.time = 30.0
        self.is_started = False
        self.task = None
        self.start_time = None
        self.logger = logging.getLogger('wappy')

    async def start(self, period):
        if not self.is_started:
            self.time = period
            self.is_started = True
            # Start task to call func periodically:
            self.task = asyncio.ensure_future(self._run())
            # self.logger.info("------------ Started --------------")

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self.task.cancel()
            # self.logger.info("------------ Stoped --------------")
            with suppress(asyncio.CancelledError):
                await self.task

    def is_started(self):
        return self.is_started

    async def _run(self):
        while True:
            await asyncio.sleep(self.time)
            # self.logger.info(" time to call function: "
            # .format(self.func.__name__))
            self.func()
            if not self.repeat:
                break
