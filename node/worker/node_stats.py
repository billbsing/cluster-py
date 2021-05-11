#!/usr/bin/env  python3

import cpuinfo
import psutil
import rpyc
import os
import time

from threading import Thread

NODE_STATS_PORT = 18880

class NodeStats(rpyc.Service):

    def exposed_get_cpu(self):
        cpu_percent = psutil.cpu_percent(interval=None)
        return cpu_percent

    def exposed_get_cpu_count(self):
        return os.cpu_count()

    def exposed_get_temperatures(self):
        temp = psutil.sensors_temperatures()
        result = 0
        for name, sensor in temp.items():
            item = sensor[0]
            if item and hasattr(item, 'current'):
                result = item.current
        return result

    def exposed_get_virtual_memory(self):
        value = psutil.virtual_memory()
        return {
            'test': 0.0,
            'total': value.total, 
            'available': value.available, 
            'percent': float(value.percent), 
            'used': value.used, 
            'free': value.free, 
            'active': value.active, 
            'inactive': value.inactive, 
            'buffers': value.buffers, 
            'cached': value.cached, 
            'shared': value.shared, 
            'slab': value.slab
        }

    def exposed_get_cpu_info(self):
        return cpuinfo.get_cpu_info()

def main():
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(NodeStats, port=NODE_STATS_PORT)
    server.start()

if __name__ == "__main__":
    main()
