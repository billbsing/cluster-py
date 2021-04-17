#!/usr/bin/env  python3

import cpuinfo
import psutil
import rpyc

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
                print(item)
                result = item.current
        return result

    def exposed_get_cpu_info(sefl):
        return cpuinfo.get_cpu_info()

    def exposed_do_close(self):
        if server:
            server.close()

def main():
    global server
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(NodeStats, port=NODE_STATS_PORT)
    server.start()

if __name__ == "__main__":
    main()
