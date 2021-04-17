"""

Cluster Class

"""

import logging
import re
import os
import yaml

from cluster.node import Node


logger = logging.getLogger(__name__)

class Cluster:

    def __init__(self):
        self._config = None
        self._nodes = {}
        self._worker_path = None

    def load_config(self, config_filename):
        self._config = None
        if os.path.exists(config_filename):
            with open(config_filename, 'r') as fp:
                self._config = yaml.safe_load(fp)
                #self._worker_path = os.path.expandvars(self._config['worker_path'])
                self._worker_path = self._config['worker_path']
                self.load_nodes()
        return self._config

    def load_nodes(self):
        index = 1
        for item in self.config['nodes']:
            node = Node(index, item['name'], item['hostname'], item['username'], self.config['key_file'], self._worker_path) 
            self.nodes[node.index] = node
            index += 1

    @property
    def nodes(self):
        return self._nodes

    @property
    def config(self):
        return self._config

    @property
    def worker_path(self):
        return self._worker_path
