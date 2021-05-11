#!/usr/bin/env      python3


import argparse
import cpuinfo
import logging
import math
import os
import psutil
import rpyc
import time

from multiprocessing import Process, Queue

from cluster import (
    Cluster,
    Worker
)

from threading import Lock
from blessed import Terminal

BYTES_PER_KB = 1000

DEFAULT_CONFIG_FILENAME = 'cluster.conf'
NODE_STATS_WORKER_PATH = os.path.join(os.path.dirname(__file__), 'worker')
NODE_STATS_PORT = 18880
NODE_STATS_APP_NAME = 'node_stats.py'

logger = logging.getLogger(__name__)
terminal = None
lock = Lock()

DISPLAY_FIELDS = {
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
    # 'cpu_count_2': {
    #     'title': 'count',
    #     'width': 5
    # },
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
    set_field_value(fields, 'node', f'*{controller.name}*')

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
    # set_field_value(fields, 'cpu_count_2', os.cpu_count())
    set_field_value(fields, 'cpu_speed', cpu_info['hz_actual_friendly'])
    set_field_value(fields, 'cpu_brand', cpu_info['brand_raw'])

def fill_worker_stats(fields, index, node_name, cpu, cpu_count, memory, temp, cpu_info):
    set_field_value(fields, 'index', index)
    set_field_value(fields, 'node', node_name)

    set_field_value(fields, 'cpu_percent', cpu)

    set_field_value(fields, 'memory_percent', memory['percent'])
    set_field_value(fields, 'memory_total', show_size_as_text(memory['total']))

    set_field_value(fields, 'temperature', temp)

    set_field_value(fields, 'cpu_arch', cpu_info['arch'])
    set_field_value(fields, 'cpu_bits', cpu_info['bits'])
    set_field_value(fields, 'cpu_count', cpu_info['count'])
    # set_field_value(fields, 'cpu_count_2', cpu_count)
    set_field_value(fields, 'cpu_speed', cpu_info['hz_actual'])
    set_field_value(fields, 'cpu_brand', cpu_info['brand'])

def node_update_proc(x, y, index, node, is_restart, display_queue, control_queue):

    display_queue.put([x, y, f'{index:4} starting node {node.name}' + (' ' * 130)])

    worker = Worker(node, NODE_STATS_WORKER_PATH, NODE_STATS_APP_NAME, NODE_STATS_PORT)
    connection = worker.startup(is_restart)
    if not connection:
        display_queue.put([x, y, f'cannot connect to node {node.name}'])

    fields = DISPLAY_FIELDS
    while control_queue.empty():
        cpu = connection.root.get_cpu()
        cpu_count = connection.root.get_cpu_count()
        memory = connection.root.get_virtual_memory()
        try:
            temp = connection.root.get_temperatures()
        except:
            temp = 0.0
        cpu_info = connection.root.get_cpu_info()
        fill_worker_stats(fields, index, node.name, cpu, cpu_count, memory, temp, cpu_info)

        display_queue.put([x, y, generate_line_stats(fields)])
        time.sleep(1)
    connection.close()

def local_update_proc(x, y, index, controller, display_queue, is_active_queue):
    fields = DISPLAY_FIELDS
    while is_active_queue.empty():
        fill_local_stats(fields, index, controller)
        display_queue.put([x, y, generate_line_stats(fields)])
        time.sleep(1)

def show_size_as_text(size):
    """
    Show the size in text readable form.
    :return: the size in bytes, kb, mb e.t.c depending on the quantit of size.
    """
    result = f'{size} Bytes'
    values = [
        'KB',
        'MB',
        'GB',
        'TB',
    ]

    for index in range(len(values)):
        max_size = math.pow(BYTES_PER_KB, index + 1)
        if size < max_size: 
            break
        format_size = size / max_size
        result = f'{format_size:.2f} {values[index]}'

    return result

def main():

    global terminal, lock

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

    terminal = Terminal()
    display_queue = Queue()
    control_queue = Queue()
    fields = DISPLAY_FIELDS
    proc_list = []
    index = 0
    x = 0
    y = terminal.height - len(cluster.nodes)  - 3
    with terminal.location(x, y):
        print(generate_line_header(fields).rstrip())
    y += 1

    proc = Process(target=local_update_proc, args=(x, y, index, cluster.controller, display_queue, control_queue))
    proc.start()
    proc_list.append(proc)
    y += 1
    index += 1
    for node in cluster.nodes:
        proc = Process(target=node_update_proc, args=(x, y, index, node, args.restart, display_queue, control_queue))
        proc.start()
        proc_list.append(proc)
        y += 1
        index += 1

    while True:

        while not display_queue.empty():
            item = display_queue.get()
            with terminal.location(item[0], item[1]):
                print(item[2].rstrip())
            
        with terminal.cbreak(), terminal.hidden_cursor():
            inp = terminal.inkey(0.5)
            if inp:
                break
           
    control_queue.put('exit')
    for proc in proc_list:
        proc.join()


if __name__ == '__main__':
    main()
