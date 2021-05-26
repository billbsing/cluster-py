#!/usr/bin/env  python3

import cpuinfo
import math
import random
import rpyc

WORKER_PORT = 18883


class PICalculatorWorker(rpyc.Service):

    def exposed_calculate(self, size):
        result = 0
        for index in range(size):
            # x = random.uniform (-1.0, 1.0)
            # y = random.uniform (-1.0, 1.0)
            # distance = math.hypot(x, y)
            x = random.random()
            y = random.random()
            distance = math.sqrt(x**2 + y**2)
            if distance < 1.0:
                result += 1
        return result

    def exposed_get_cpu_count(self):
        info = cpuinfo.get_cpu_info()
        return info['count']        

def main():
    from rpyc.utils.server import ForkingServer
    server = ForkingServer(PICalculatorWorker, port=WORKER_PORT)
    server.start()



if __name__ == "__main__":
    main()
