"""

Cluster Controller

"""

import logging


logger = logging.getLogger(__name__)

class Controller:

    def __init__(self, name, hostname, username):
        self._name = name
        self._hostname = hostname
        self._username = username

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
