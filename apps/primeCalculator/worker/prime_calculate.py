#!/usr/bin/env  python3

import cpuinfo
import math
import redis
import rpyc

PRIME_CALC_PORT = 18882


class PrimeCalculatorWorker(rpyc.Service):
    def __init__(self):
        rpyc.Service.__init__(self)
        self._redis = None

    def on_connect(self, connection):
        print('connect')

    def on_disconnect(self, connection):
        print('disconnect')

    def exposed_do_open(self, host, port, db):
        self._redis = redis.Redis(host=host, port=port, db=db)
        return self._redis.ping()

    def exposed_do_close(self):
        if self._redis:
            self._redis = None

    def exposed_calculate(self, data_name, from_number, to_number):
        prime_numbers = self.calculate_prime(from_number, to_number)
        if self._redis:
            for prime_number in prime_numbers:
                self._redis.sadd(data_name, prime_number)
            # self._redis.rpush(list_name, *prime_numbers)
            return prime_numbers
        return None

    def exposed_get_cpu_count(self):
        info = cpuinfo.get_cpu_info()
        return info['count']        

    def calculate_prime(self, from_number, to_number):
        result = []
        for number in range(from_number, to_number):
            if self.is_prime(number):
                result.append(number)
        return result

    def is_prime(self, number):
        if number < 2:
            return False

        index = 2
        limit = int(math.sqrt(number)) + 1
        while index < limit:
            if number % index == 0:
                return False
            index += 1

        return True

def main():
    from rpyc.utils.server import ForkingServer
    server = ForkingServer(PrimeCalculatorWorker, port=PRIME_CALC_PORT)
    server.start()



if __name__ == "__main__":
    main()
