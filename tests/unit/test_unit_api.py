
import api
import datetime
import hashlib
import unittest
import unittest.mock as mock
from libtools import cases


class TestUnitApiCheckAuth(unittest.TestCase):
    def setUp(self) -> None:
        self.request = {"account": "horns&hoofs",
                        "login": "h&f",
                        "method": "clients_interests",
                        "token": "55cc9ce545bcd144300fe"
                                 "9efc28e65d415b923ebb6b"
                                 "e1e19d2750a2c03e80dd209"
                                 "a27954dca045e5bb12418e7"
                                 "d89b6d718a9e35af34e14e1"
                                 "d5bcd5a08f21fc95",
                        "arguments": {}}
        self.method = api.MethodRequest

    def test_check_auth_admin(self):
        self.request['login'] = 'admin'
        self.request['token'] = hashlib.sha512(bytes(datetime.datetime.now().strftime("%Y%m%d%H")
                                                     + api.ADMIN_SALT, encoding='utf-8')).hexdigest()
        self.assertEqual(api.check_auth(self.method(self.request)), True)

    def test_check_auth_user(self):
        self.assertEqual(api.check_auth(self.method(self.request)), True)



if __name__ == '__main__':
    unittest.main()
