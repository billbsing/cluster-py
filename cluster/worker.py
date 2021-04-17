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
        self._connection = None

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

    def connect(self):
        self._connection = None
        try:
            self._connection = rpyc.connect(self._node.hostname, self._port)
            logger.debug(f'connected {self._node.hostname}')
        except Exception as e:
            self._connection = None
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
        self._connection = None

    def startup(self, is_restart=False, connection_timeout=CONNECTION_TIMEOUT):
        connection = self.connect()
        if connection and is_restart:
            logger.debug(f'closing {self._node.hostname}');
            try:
                self.connection.root.do_close()
                self.close()
            except Exception as e:
                pass
            connection = None

        if not connection:
            logger.debug(f'rsync worker path')
            result = self._node.sync(self._path)
            logger.debug(f'sync output: {result}')
            logger.debug(f'starting worker {self._node.hostname}...')
            proc = self.start()
            timeout = time.time() + connection_timeout
            while timeout > time.time():
                connection = self.connect()
                if connection:
                    break
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

    @property
    def connection(self):
        return self._connection

    def __str__(self):
        return f'{self._node}: {self._filename}:{self._port}'
