"""

Worker Class

"""

import logging
import re
import rpyc
import subprocess
import time
import os

CONNECTION_TIMEOUT = 10

logger = logging.getLogger(__name__)

class Worker:

    def __init__(self, node, path, app_name, port):
        self._node = node
        self._path = path
        self._app_name = app_name
        self._port = port

    def start(self):
        command = os.path.join(self._node.worker_path, self._app_name)
        line = ['ssh',
            '-i',
            self._node.key_file,
            self._node.username_hostname,
            command
        ]
        logger.debug(f'ssh line: {" ".join(line)}')
        proc = subprocess.Popen(line, stdout=subprocess.PIPE)
        return proc

    def connect(self, config={}):
        connection = None
        try:
            connection = rpyc.connect(self._node.hostname, self._port, config=config)
            logger.debug(f'connected {self._node.hostname}')
        except Exception as e:
            logger.debug(f'connection error: {e}')
        return connection

    def startup(self, is_restart=False, connection_timeout=CONNECTION_TIMEOUT):
        proc = None
        if is_restart:
            logger.debug(f'need to do restart so closing {self._node.hostname}');
            try:
                line = f'pkill -f {self._app_name}'
                self._node.execute(line)
            except Exception as e:
                logger.debug(f'close connection {e}')

            logger.debug(f'rsync worker path')
            result = self._node.sync(self._path)
            logger.debug(f'sync output: {result}')

        connection = self.connect()
        if not connection:
            logger.debug(f'starting worker {self._node.hostname}...')
            proc = self.start()

            timeout = time.time() + connection_timeout
            logger.debug('waiting for connection')
            while timeout > time.time():
                connection = self.connect()
                if connection:
                    logger.debug('connected')
                    break
            if proc:
                proc.kill()
        return connection 

    @property
    def node(self):
        return self._node

    @property
    def path(self):
        return self._path

    @property
    def app_name(self):
        return self._app_name

    @property
    def port(self):
        return self._port

    def __str__(self):
        return f'{self._node}: {self._filename}:{self._port}'
