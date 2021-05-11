#!/usr/bin/env      python3

import argparse
import os
import subprocess
import yaml

from multiprocessing import Process


from cluster import (
    Cluster,
    Worker
)

DEFAULT_CONFIG_FILENAME = 'cluster.conf'

COMMAND_LIST = ['exec', 'sync', 'poweroff']

def node_command(cluster, node, command, params):

    if command == 'exec':
        if not params:
            print('you need to pass a command to execute')
            return
        result = node.execute(params[0])
        print(f'{node}: exec {params[0]}')
        print(result)
    elif command == 'sync':
        result = node.sync(cluster.worker_path)
        print(f'{node}: rsync {cluster.worker_path}')
        print(result)
    elif command == 'poweroff':
        result = node.execute('sudo poweroff')
        print(f'{node}: exec sudo poweroff')
        print(result)


def main():


    parser = argparse.ArgumentParser(description='Execute command on all nodes')

    parser.add_argument('-c', '--config',
        default=DEFAULT_CONFIG_FILENAME,
        help='config file. Default {DEFAULT_CONFIG_FILENAME}'
    )

    parser.add_argument('--count',
        help='number of nodes to operate on. Default: All nodes'
    )

    parser.add_argument('command',
        help='command to run for each node'
    )

    parser.add_argument('params', 
        nargs='*',
        help='remote command to execute'
    )

    args = parser.parse_args()
    cluster = Cluster()

    if not cluster.load_config(args.config):
        print(f'cannot find config file {args.config}')
        return

    count = 0
    if args.count:
        count = int(args.count)
    node_count = 0
    command = args.command.lower()
    if command not in COMMAND_LIST:
        print(f'unkown command "{args.command}"')

    proc_list = []

    for node in cluster.nodes:
        if node_count >= count and count > 0:
            break
        node_count += 1
        command = args.command.lower()
        proc = Process(target=node_command, args=(cluster, node, command, args.params))
        proc_list.append(proc)
        proc.start()


    for proc in proc_list:
        proc.join()

if __name__ == '__main__':
    main()
