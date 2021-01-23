"""
    configuration
"""

import os.path
import logging
from utils import dotDict
import toml


class IOCertsError(Exception):
    pass


class Configuration:
    def __init__(self, filename):
        logging.basicConfig(level=logging.DEBUG, datefmt='%m-%d %H:%M')
        logger = logging.getLogger(__name__)

        searchPath = ["/etc/", "./"]
        for p in searchPath:
            confFile = p + filename
            if os.path.isfile(confFile):
                logger.info("Found configuration file: '{}'".format(confFile))
                try:
                    self._conf = toml.load(confFile)
                    if not self.conf.certs.skip:
                        self._checkIfCertificatesExist()
                    return
                except IOError:
                    logger.warn("Invalid configuration file '{}' load default."
                                .format(confFile))
                    self._conf = self._defaultConfiguration()
                    if not self.conf.certs.skip:
                        self._checkIfCertificatesExist()
                    return
                except IOCertsError as e:
                    logger.error(e)
                    raise SystemExit

        logger.warn("No configuration file was found, load default")
        self._conf = self._defaultConfiguration()
        if not self.conf.certs.skip:
            self._checkIfCertificatesExist()

    def _defaultConfiguration(self):
        conf = {
            'path': {
                'project': "/opt/wappy/",
                'certificates': "/opt/wappy/certificates/",
                'log': "/opt/wappy/log/"
                },
            'certs': {
                'ca_crt': "ca.crt",
                'client_crt': "client.crt",
                'client_key': "client.key"
                },
            'backend': {
                'network_id': "12345",
                'host': "collector.wappsto.com",
                'port': 443
            }
        }
        return conf

    def _checkIfCertificatesExist(self):
        ca_crt = self.conf.path.certificates + self.conf.certs.ca_crt
        client_crt = self.conf.path.certificates + self.conf.certs.client_crt
        client_key = self.conf.path.certificates + self.conf.certs.client_key

        if not os.path.exists(client_crt):
            raise IOCertsError("Can not find {}".format(ca_crt))
        if not os.path.exists(client_crt):
            raise IOCertsError("Can not find {}".format(client_crt))
        if not os.path.exists(client_key):
            raise IOCertsError("Can not find {}".format(client_key))

    @property
    def conf(self):
        path = dotDict(self._conf['path'])
        certs = dotDict(self._conf['certs'])
        backend = dotDict(self._conf['backend'])
        return dotDict({
            'path': path,
            'certs': certs,
            'backend': backend
        })


wappy = Configuration("wappy.toml")
