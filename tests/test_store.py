import unittest
import store
import unittest.mock as mock


class TestStore(unittest.TestCase):

    @mock.patch('store.Store')
    def test_get(self):
        cls = store.WorksRedis()
        cls.server.connection = False
        mock_stor = store.Store(cls)
        with self.assertRaises(ConnectionError):
            mock_stor.get('key')

if __name__ == "__main__":
    unittest.main()