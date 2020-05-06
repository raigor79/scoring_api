import redis
import time
from functools import lru_cache


class WorksRedis:

    def __init__(self, hostname='localhost', port=6379, socket_timeout=1, socket_connect_timeout=1):
        self.h_name = hostname
        self.port = port
        self.timeout = socket_timeout
        self.connect_timeout = socket_connect_timeout
        self.server = redis.Redis(host=self.h_name,
                           port=self.port,
                           socket_timeout=self.timeout,
                           socket_connect_timeout=self.connect_timeout,
                           decode_responses=True)


    def set(self, key, value, expiry=60):
        try:
            return self.server.set(key, value, expiry)
        except redis.TimeoutError:
            raise TimeoutError
        except redis.ConnectionError:
            raise ConnectionError

    def get(self, key):
        try:
            return self.server.get(key)
        except redis.TimeoutError:
            raise TimeoutError
        except redis.ConnectionError:
            raise ConnectionError


class Store:
    cache_size = 10

    def __init__(self, cls, attempt_request=3, delay=0.1, cache_size=10):
        self.store = cls
        self.attempt_request = attempt_request
        self.delay = delay
        self.cache_size = cache_size

    def get(self, key):
        for attempt in range(self.attempt_request):
            try:
                return self.store.get(key)
            except (TimeoutError, ConnectionError):
                time.sleep(attempt * self.delay)
        else:
            raise TimeoutError

    def cache_set(self, key, value, expire):
        for attempt in range(self.attempt_request):
            try:
                return self.store.set(key, value, expire)
            except (TimeoutError, ConnectionError):
                time.sleep(attempt * self.delay)

    @lru_cache(maxsize=cache_size)
    def cache_get(self, key):
        for attempt in range(self.attempt_request):
            try:
                return self.store.get(key)
            except (TimeoutError, ConnectionError):
                time.sleep(attempt * self.delay)

