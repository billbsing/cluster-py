#!/usr/bin/env      python3


import argparse
import cpuinfo
import logging
import math
import os
import psutil
import time

from cluster import (
    Cluster,
    Worker
)

from blessed import Terminal

BYTES_PER_KB = 1000

DEFAULT_CONFIG_FILENAME = 'cluster.conf'
NODE_STATS_WORKER_PATH = os.path.join(os.path.dirname(__file__), 'worker')
NODE_STATS_PORT = 18880
NODE_STATS_APP_NAME = 'node_stats.py'

logger = logging.getLogger(__name__)

fields = {
    'index' : {
        'title': '#',
        'width': 4,
        'title_format': '>4'
    },
    'node': {
        'title': 'node',
        'width': 20
    },
    'cpu_percent': {
        'title': '%cpu',
        'width': 5,
        'format': '5.1f',
        'title_format': '>5'
    },
    'temperature': {
        'title': 'temp',
        'width': 5,
        'format': '5.1f',
        'title_format': '>5'
    },
    'memory_percent': {
        'title': '%mem',
        'width': 5,
        'format': '5.1f',
        'title_format': '>5'
    },
    'memory_total': {
        'title': 'Total Mem',
        'width': 10,
        'format': '>10',
        'title_format': '>10'
    },
    'cpu_arch': {
        'title': 'arch',
        'width': 10,
        'format': '>10'
    },
    'cpu_bits': {
        'title': 'bits',
        'width': 4
    },
    'cpu_count': {
        'title': 'count',
        'width': 5
    },
    'cpu_speed': {
        'title': 'speed',
        'width': 15,
        'format': '>15'
    },
    'cpu_brand': {
        'title': 'brand',
        'width': 40,
        'format': '>40'
    },
} 

def set_field_value(fields, name, value):
    field = fields[name]
    format_field = field['width']
    if 'format' in field:
        format_field = field['format']

    fields[name]['value'] = '{0:{format_field}}'.format(value, format_field=format_field)

def generate_line_header(fields):
    line = []
    for name, field in fields.items():
        title = field['title']
        format_field = field['width']
        if 'title_format' in field:
            format_field = field['title_format']
        elif 'format' in field:
            format_field = field['format']
        line.append('{0:{format_field}}'.format(title, format_field=format_field))
    return ' '.join(line)


def generate_line_stats(fields):
    line = []
    for name, item in fields.items():
        line.append(item['value'])
    return ' '.join(line)

def fill_local_stats(fields, index, controller):
    set_field_value(fields, 'index', index)
    set_field_value(fields, 'node', controller.name)

    cpu_percent = psutil.cpu_percent(interval=None)
    set_field_value(fields, 'cpu_percent', cpu_percent)

    memory = psutil.virtual_memory()
    set_field_value(fields, 'memory_percent', memory.percent)
    set_field_value(fields, 'memory_total', show_size_as_text(memory.total))

    temp = psutil.sensors_temperatures()
    set_field_value(fields, 'temperature', temp['cpu_thermal'][0].current)


    cpu_info = cpuinfo.get_cpu_info()
    set_field_value(fields, 'cpu_arch', cpu_info['arch'])
    set_field_value(fields, 'cpu_bits', cpu_info['bits'])
    set_field_value(fields, 'cpu_count', cpu_info['count'])
    set_field_value(fields, 'cpu_speed', cpu_info['hz_actual_friendly'])
    set_field_value(fields, 'cpu_brand', cpu_info['brand_raw'])

def fill_worker_stats(fields, index, worker):
    set_field_value(fields, 'index', index)
    set_field_value(fields, 'node', worker.node.name)

    cpu = worker.connection.root.get_cpu()
    set_field_value(fields, 'cpu_percent', cpu)

    memory = worker.connection.root.get_virtual_memory()
    set_field_value(fields, 'memory_percent', memory['percent'])
    set_field_value(fields, 'memory_total', show_size_as_text(memory['total']))

    try:
        temp = worker.connection.root.get_temperatures()
    except:
        temp = 0.0

    set_field_value(fields, 'temperature', temp)

    cpu_info = worker.connection.root.get_cpu_info()
    set_field_value(fields, 'cpu_arch', cpu_info['arch'])
    set_field_value(fields, 'cpu_bits', cpu_info['bits'])
    set_field_value(fields, 'cpu_count', cpu_info['count'])
    set_field_value(fields, 'cpu_speed', cpu_info['hz_actual'])
    set_field_value(fields, 'cpu_brand', cpu_info['brand'])

def show_size_as_text(size):
    """
    Show the size in text readable form.
    :return: the size in bytes, kb, mb e.t.c depending on the quantit of size.
    """
    result = f'{size} Bytes'
    items = [
        (BYTES_PER_KB, 'KB'),
        (math.pow(BYTES_PER_KB, 2), 'MB'),
        (math.pow(BYTES_PER_KB, 3), 'GB'),
        (math.pow(BYTES_PER_KB, 4), 'TB'),
    ]

    for item in items:
        if size < item[0]:
            break
        format_size = size / item[0]
        result = f'{format_size:.2f} {item[1]}'

    return result

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
        y = term.height - len(workers)  - 3

        with term.location(x, y):
            print(generate_line_header(fields))

        y += 1
        index = 0
        fill_local_stats(fields, index, cluster.controller)

        with term.location(x, y):
            print(generate_line_stats(fields))
        index += 1
        y += 1

        for worker in workers:
            fill_worker_stats(fields, index, worker)

            with term.location(x, y):
                print(generate_line_stats(fields))
            index += 1
            y += 1

        with term.cbreak(), term.hidden_cursor():
            inp = term.inkey(1)
            if inp:
                break


if __name__ == '__main__':
    main()
