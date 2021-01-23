#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""

import sys
import asyncio
import logging
import signal
from wappclient import WappClient, bastard_connect
import ssl


def signalHandler(signal, frame):
    sys.exit(0)


def startWappy():

    loop = asyncio.get_event_loop()
    # loop.set_debug(enabled=1)

    logger = logging.getLogger('wappy')
    logger.info("Starting 'Wappy'!")
    signal.signal(signal.SIGINT, signalHandler)

    try:
        bastard = WappClient(loop)
        logger.info('')
        loop.run_until_complete(bastard_connect(bastard, loop))
        loop.run_forever()
    except ssl.SSLError:
        logger.info("")
        logger.info('SSL exception, check if provided certificates are valid!')
        logger.info("")
    finally:
        logger.info('-- Closing event loop -- Bye!')
        loop.close()


if __name__ == '__main__':
    if sys.version_info.major > 2 and sys.version_info.minor > 4:
        print("Python version: {}.{}.{}".format(sys.version_info.major,
                                                sys.version_info.minor,
                                                sys.version_info.micro))
    else:
        print('***********************************************************')
        print('You need python version 3.5 or later! .....')
        print('***********************************************************')
        raise SystemExit

    startWappy()
