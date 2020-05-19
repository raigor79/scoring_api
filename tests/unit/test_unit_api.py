import api
import datetime
import hashlib
import unittest
from libtools import cases
import unittest.mock as mock


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

    def test_ok_check_auth_admin(self):
        self.request['login'] = 'admin'
        self.request['token'] = hashlib.sha512(bytes(datetime.datetime.now().strftime("%Y%m%d%H")
                                                     + api.ADMIN_SALT, encoding='utf-8')).hexdigest()
        self.assertEqual(api.check_auth(self.method(self.request)), True)

    def test_ok_check_auth_user(self):
        self.assertEqual(api.check_auth(self.method(self.request)), True)

    def test_invalid_check_auth_admin(self):
        self.request['login'] = 'admin'
        self.request['token'] = "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209"
        self.assertEqual(api.check_auth(self.method(self.request)), False)

    def test_invalid_check_auth_user(self):
        self.request['login'] = 'h&f'
        self.request['token'] = "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209"
        self.assertEqual(api.check_auth(self.method(self.request)), False)


class TestUnitApiClientsInterestsRequest(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.settings = {}
        self.response = {}
        api._get_interests = mock.MagicMock(return_value=['tv', 'sport'])

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_clients_interests_request(self, arguments):
        response, code = api.clients_interests_request(self.settings, arguments, self.context)
        self.assertEqual(api.OK, code)
        self.assertEqual({client_ids:['tv','sport'] for client_ids in arguments['client_ids']}, response)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_clients_interests_request(self, arguments):
        response, code = api.clients_interests_request(self.settings, arguments, self.context)
        self.assertEqual(api.INVALID_REQUEST, code)


class TestUnitApiOnlineScoreRequest(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.settings = {}
        self.response = {}
        api._get_score = mock.MagicMock(return_value=5)

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_online_score_request(self, arguments):
        response, code = api.online_score_request(self.settings, arguments, self.context)
        self.assertEqual(api.OK, code)
        self.assertEqual({'score': 5}, response)

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_online_score_request(self, arguments):
        response, code = api.online_score_request(self.settings, arguments, self.context)
        self.assertEqual(api.INVALID_REQUEST, code)


class TestUnitApiMethodHandler(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.settings = {}
        self.response = {}
        self.headers = {}
        api._get_score = mock.MagicMock(return_value=42)
        api._get_interests = mock.MagicMock(return_value=42)

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_method_handler(self, arguments):
        api.check_auth = mock.MagicMock(return_value=True)
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        api.MethodRequest.validated_argument = mock.MagicMock(return_value=None)
        response, code = api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)
        self.assertEqual(api.OK, code)
        self.assertEqual({'score': 42}, response)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_request_method_handler(self, arguments):
        api.check_auth = mock.MagicMock(return_value=True)
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        response, code = api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth_method_handler(self, request):
        response, code = api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)
        self.assertEqual(api.FORBIDDEN, code)


if __name__ == '__main__':
    unittest.main()
