#!/usr/bin/env      python3


import argparse
import logging
import os
import time

from cluster import (
    Cluster,
    Worker
)

from blessed import Terminal

DEFAULT_CONFIG_FILENAME = 'cluster.conf'
NODE_STATS_WORKER_PATH = os.path.join(os.path.dirname(__file__), 'worker')
NODE_STATS_PORT = 18880
NODE_STATS_APP_NAME = 'node_stats.py'

logger = logging.getLogger(__name__)

def main():

    parser = argparse.ArgumentParser(description='Node stats')

    parser.add_argument('-c', '--config',
        default=DEFAULT_CONFIG_FILENAME,
        help='config file. Default {DEFAULT_CONFIG_FILENAME}'
    )

    parser.add_argument('--count',
        help='number of nodes to operate on. Default: All nodes'
    )

    parser.add_argument('-d', '--debug',
        action='store_true',
        help='Show debug information. Default: False'
    )

    parser.add_argument('--restart',
        action='store_true',
        help='force restart of node servers. Default: False'
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    cluster = Cluster()

    if not cluster.load_config(args.config):
        print(f'cannot find config {args.config} file')
        return

    term = Terminal()

    workers = []
    for node_name, node in cluster.nodes.items():
        worker = Worker(node, NODE_STATS_WORKER_PATH, NODE_STATS_APP_NAME, NODE_STATS_PORT)
        if not worker.startup(args.restart):
            print(f'cannot connect to node {node.name}')
            return
        workers.append(worker)

    while True:
        x = 0
        y = term.height - len(workers) - 1

        with term.location(x, y - 1):
            print('   # node                  %cpu          temperature       arch bits count           speed                                 cpu name ')

        
        index = 1
        for worker in workers:
            cpu = worker.connection.root.get_cpu()
            try:
                temp = worker.connection.root.get_temperatures()
            except:
                temp = 0

            cpu_info = worker.connection.root.get_cpu_info()
            with term.location(x, y):
                print(f'{index:4} {worker.node.name:20} {cpu:5} {temp:20.1f} {cpu_info["arch"]:>10} {cpu_info["bits"]:4} {cpu_info["count"]:5} {cpu_info["hz_actual"]:>15} {cpu_info["brand"]:>40}')
            index += 1
            y += 1

        with term.cbreak(), term.hidden_cursor():
            inp = term.inkey(1)
            if inp:
                break


if __name__ == '__main__':
    main()
