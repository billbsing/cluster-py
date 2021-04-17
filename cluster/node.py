"""

Node Class

"""

import logging
import subprocess
import os

logger = logging.getLogger(__name__)

class Node:

    def __init__(self, index, name, hostname, username, key_file, worker_path):
        self._index = index
        self._name = name
        self._hostname = hostname
        self._username = username
        self._key_file = os.path.expandvars(key_file)
        self._worker_path = worker_path

    def execute(self, command):
        logger.debug(f'ssh {self.hostname} {command}')
        line = ['ssh',
            '-i',
            self.key_file,
            self.username_hostname,
            command
        ]
        p = subprocess.Popen(line, stdout=subprocess.PIPE)
        out = p.stdout.read()
        return out.decode()

    def sync(self, source_path):
        logger.debug(f'rsync {source_path} {self.hostname}')

        line = ['rsync',
            '--archive',
            '--recursive',
            '--verbose',
            # '--delete',
            '--rsh',
            f'ssh -i {self.key_file}',
            source_path,
            f'{self.username_hostname}:'
        ]
        p = subprocess.Popen(line, stdout=subprocess.PIPE)
        out = p.stdout.read()
        return out.decode()

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._name

    @property
    def hostname(self):
        return self._hostname

    @property
    def username_hostname(self):
        return f'{self._username}@{self._hostname}'

    @property
    def username(self):
        return self._username

    @property
    def key_file(self):
        return self._key_file

    @property
    def worker_path(self):
        return self._worker_path

    def __str__(self):
        return f'{self.name} {self.username_hostname}'
