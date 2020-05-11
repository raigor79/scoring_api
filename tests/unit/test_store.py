import unittest
import store
import time
import unittest.mock as mock
from libtools import cases


class TestStore(unittest.TestCase):

    def setUp(self) -> None:

        @cases([{'i:1': '1'}, {'i:2': 'age'}, {'i:3': 'tv'}])
        def filling(arguments):
            for key in arguments.keys():
                self.storage.cache_set(key, arguments[key], expire=1)

        self.attempt_request = 4
        self.cache_size = 2
        self.storage_redis = store.WorksRedis()
        self.storage = store.Store(self.storage_redis,
                                   attempt_request=self.attempt_request,
                                   cache_size=self.cache_size)
        filling()

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

    @cases([{'i1': 1}, {'i2': ["cars", "pets"]}, {'i3': '1234'}])
    @mock.patch.object(store.redis.Redis, 'get')
    def test_mocked_store_cache_get_and_get(self, argument, mocked_get):
        key = list(argument.keys())[0]
        mocked_get.return_value = argument[key]
        self.assertEqual(self.storage.cache_get(key), argument[key])
        mocked_get.assert_called_once_with(key)
        self.assertEqual(self.storage.get(key), argument[key])
        mocked_get.assert_called_with(key)

    def test_cache_note_false(self):
        self.assertEqual(self.storage.get('i:1'), '1')
        time.sleep(1)
        self.assertEqual(self.storage.get('i:1'), None)

    def test_cache_note_true(self):
        self.assertEqual(self.storage.cache_get('i:1'), '1')
        time.sleep(1.1)
        self.assertEqual(self.storage.cache_get('i:3'), None)
        self.assertEqual(self.storage.cache_get('i:2'), None)
        self.assertEqual(self.storage.cache_get('i:1'), '1')

class TestWorksRedis(unittest.TestCase):

    def setUp(self) -> None:
        self.storage_redis = store.WorksRedis()

    def test_connect_error(self):
        self.storage_redis.get = mock.MagicMock(side_effect=ConnectionError)
        self.storage_redis.set = mock.MagicMock(side_effect=ConnectionError)
        with self.assertRaises(ConnectionError):
            self.storage_redis.get('key')
            self.storage_redis.set('key', 'value', 10)

    @mock.patch.object(store.WorksRedis, 'set')
    def test_set(self, mocked_set):
        mocked_set.return_value = None
        self.assertEqual(self.storage_redis.set('i:1', 'value', 1), None)

    @mock.patch.object(store.WorksRedis, 'get')
    def test_get(self, mocked_get):
        mocked_get.return_value = '10'
        self.assertEqual(self.storage_redis.get('i:1'), '10')


if __name__ == "__main__":
    unittest.main()