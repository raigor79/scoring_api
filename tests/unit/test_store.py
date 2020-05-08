import unittest
import store
import time
import functools
import unittest.mock as mock


def cases(cases, count={}):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                try:
                    new_args = args + (c if isinstance(c, tuple) else (c,))
                    f(*new_args)
                except Exception as er:
                    count[f.__name__] = c.__repr__()
                    print('{}. function failure {}  at value {}'.format(len(count),
                                                                        f.__name__,
                                                                        count[f.__name__]))
                    raise er
        return wrapper
    return decorator


class TestStore(unittest.TestCase):

    def setUp(self) -> None:
        self.attempt_request = 4
        self.cache_size = 2
        self.storage_redis = store.WorksRedis()
        self.storage = store.Store(self.storage_redis,
                                   attempt_request=self.attempt_request,
                                   cache_size=self.cache_size)

    def test_connection_error(self):
        self.storage_redis.server.get = mock.MagicMock(side_effect=ConnectionError)
        self.storage_redis.server.set = mock.MagicMock(side_effect=ConnectionError)
        self.assertEqual(self.storage.cache_set('key', 'value', 60), None)
        self.assertEqual(self.storage.cache_get('key'), None)
        self.assertEqual(self.storage.store.server.get.call_count, self.attempt_request)
        self.assertEqual(self.storage.store.server.set.call_count, self.attempt_request)
        with self.assertRaises(ConnectionError):
            self.storage.get('key')
        self.assertEqual(self.storage.store.server.get.call_count, self.attempt_request * 2)

    @cases([{'i1': 1}, {'i2': ["cars", "pets"]}, {'i3': '1234'},])
    @mock.patch.object(store.redis.Redis, 'get')
    def test_mocked_store_cache_get_and_get(self, argument, mocked_get):
        for key in argument.keys():
            mocked_get.return_value = argument[key]
            self.assertEqual(self.storage.cache_get(key), argument[key])
            mocked_get.assert_called_once_with(key)
            self.assertEqual(self.storage.get(key), argument[key])
            mocked_get.assert_called_with(key)

    def test_cache(self):

        @cases([{'i:1': '1'}, {'i:2': 'age'}, {'i:3': 'tv'}])
        def filling(arguments):
            for key in arguments.keys():
                self.storage.cache_set(key, arguments[key], expire=4)

        filling()
        self.assertEqual(self.storage.cache_get('i:1'), '1')
        self.assertEqual(self.storage.get('i:1'), '1')
        time.sleep(5)
        self.assertEqual(self.storage.cache_get('i:1'), '1')
        self.assertEqual(self.storage.cache_get('i:3'), None)
        self.assertEqual(self.storage.cache_get('i:2'), None)
        self.assertEqual(self.storage.cache_get('i:1'), '1')
        self.assertEqual(self.storage.get('i:1'), None)


if __name__ == "__main__":
    unittest.main()