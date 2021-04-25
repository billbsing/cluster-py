#!/usr/bin/env  python3

import cpuinfo
import psutil
import rpyc
import time

from threading import Thread

NODE_STATS_PORT = 18880

server = None

class NodeStats(rpyc.Service):

    def exposed_get_cpu(self):
        cpu_percent = psutil.cpu_percent(interval=None)
        return cpu_percent

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

    def exposed_do_close(self):
        if server:
            server.close()

    def exposed_update(self, x, y, index, node_name, callback):
        self.x = x
        self.y = y
        self.index = index
        self.node_name = node_name
        self.callback = callback
        self.is_run = True
        self.thread = Thread(target = self.update_work)
        self.thread.start()

    def exposed_update_stop(self):   
        self.is_run = False
        try:
            self.thread.join()
        except Exception:
            pass

    def update_work(self):
        while self.is_run:
            cpu = self.exposed_get_cpu()
            memory = self.exposed_get_virtual_memory()
            temp = 0
            try:
                temp = self.exposed_get_temperature()
            except Exception:
                pass
            cpu_info = self.exposed_get_cpu_info()
            self.callback(self.x, self.y, self.index, self.node_name, cpu, memory, temp, cpu_info)
            time.sleep(1)


def main():
    global server
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(NodeStats, port=NODE_STATS_PORT)
    server.start()

if __name__ == "__main__":
    main()
