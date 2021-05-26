#!/usr/bin/env python3

import argparse
import json
import logging
import os
import queue
import random
import redis
import rpyc
import secrets
import time
from ctypes import c_int

from multiprocessing import Process, Lock, Value

from cluster import (
    Cluster,
    Worker
)


DEFAULT_MAX_NUMBER = 400000000

# DEFAULT_BLOCK_COUNT = int(DEFAULT_MAX_NUMBER  / 20)
DEFAULT_BLOCK_COUNT = 100000
DEFAULT_NODE_COUNT = 0
DEFAULT_START_NODE = 1

CPU_COUNT_FACTOR = 4

CLUSTER_CONFIG_FILENAME = 'cluster.conf'
WORKER_PATH = os.path.join(os.path.dirname(__file__), 'worker')
WORKER_PORT = 18883
WORKER_APP_NAME = 'pi_calculate.py'

logger = logging.getLogger(__name__)

def worker_thread(worker, block_count, count, total, max_total):
    connection = worker.connect(config={
        'sync_request_timeout': 60
    })
    # print(f'connected to {worker.node.name}')
    is_done = False
    while not is_done:
        value = connection.root.calculate(block_count)
        count.value = count.value + value
        total.value = total.value + block_count
        # print(count.value, total.value)
        is_done = total.value >= max_total.value
                

    connection.close()
    # print(f'finished {worker.node.name}')

def node_thread(node, is_restart, block_count, count, total, max_total):
    proc_list = []
    worker = Worker(node, WORKER_PATH, WORKER_APP_NAME, WORKER_PORT )
    connection = worker.startup(is_restart)
    if not connection:
        print(f'cannot connect to node {node.name}')
        return
    cpu_count = connection.root.get_cpu_count()
    connection.close()
    # print(f'start {worker.node.name} {cpu_count}')
    for index in range(cpu_count * CPU_COUNT_FACTOR):
        proc = Process(target=worker_thread, args=(worker, block_count, count, total, max_total))
        proc_list.append(proc)
        proc.start()

    for proc in proc_list:
        proc.join()

    # print(f'end node thread {node.name}')

def is_proc_alive(proc_list):
    for proc in proc_list:
        if proc.is_alive():
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description='PI Calculator')

    parser.add_argument('-b', '--block-count',
        default=DEFAULT_BLOCK_COUNT,
        help=f'Number of numbers to send to each node. Default: {DEFAULT_BLOCK_COUNT}'
    )

    parser.add_argument('-d', '--debug',
        action='store_true',
        help='Show debug information. Default: False'
    )

    parser.add_argument('-m', '--max',
        default=DEFAULT_MAX_NUMBER,
        help=f'Max number to calculate. Default: {DEFAULT_MAX_NUMBER}'
    )

    if os.environ.get('CLUSTER_CONF', None):
        CLUSTER_CONFIG_FILENAME = os.environ.get('CLUSTER_CONF')

    parser.add_argument('--cluster',
        default=CLUSTER_CONFIG_FILENAME,
        help=f'Config cluster file. Default: {CLUSTER_CONFIG_FILENAME}'
    )

    parser.add_argument('--count',
        default=DEFAULT_NODE_COUNT,
        help=f'Number of nodes to use as workers. Default: {DEFAULT_NODE_COUNT}'
    )

    parser.add_argument('--start',
        default=DEFAULT_START_NODE,
        help=f'Node index to start with. Default: {DEFAULT_START_NODE}'
    )

    parser.add_argument('--restart',
        action='store_true',
        help='force restart of worker servers. Default: False'
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    cluster = Cluster()

    logger.debug(f'loading cluster config file {args.cluster}')
    if not cluster.load_config(args.cluster):
        print(f'cannot find config {args.cluster} file')
        return

    if args.restart:
        print('will restart workers')

    proc_list = []
    max_number = int(args.max)
    max_node_count = int(args.count)
    node_count = 0
    node_index = 1
    current_number = 0
    block_count = args.block_count
    start_time = time.time()
    count = Value('d', 0)
    total = Value('d', 0)
    max_total = Value('d', max_number)
    lock = Lock()

    for node in cluster.nodes:
        if node_index >= int(args.start):
            proc = Process(target=node_thread, args=(node, args.restart, block_count, count, total, max_total))
            proc_list.append(proc)
            proc.start()
            node_count += 1
            if node_count >= max_node_count and max_node_count > 0:
                break
        node_index += 1

    if len(proc_list) == 0:
        print('Cannot connect to any workers')
        return

    while is_proc_alive(proc_list):
        if total.value:
            percent_done = (total.value / max_total.value) * 100
            print(f'\r{percent_done:0.1f}%', end='', flush=True)
        time.sleep(1)

    for proc in proc_list:
       proc.join()

    pi = (4.0 * count.value) / total.value


    done_time = time.time() - start_time
    print(f'\rFound {pi} numbers completed time {done_time:0.2f} seconds')


if __name__ == '__main__':
    main()
