#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
import os
from scoring import get_score, get_interests
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from weakref import WeakKeyDictionary

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


def _get_score(store=0, phone=None, email=None, birthday=None,
               gender=None, first_name=None, last_name=None):
    return get_score(store, phone, email, birthday, gender, first_name, last_name)


def _get_interests(store=0, cid=0):
    return get_interests(store, cid)


class Field(object):
    def __get__(self, instance, owner):
        return self._value.get(instance, self._value)

    def __set__(self, instance, value):
        self.valid_required_nullable(value)
        self._value[instance] = value
        self.valid_field(value)

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self._value = WeakKeyDictionary()

    def valid_required_nullable(self, value):
        if value is None and self.required:
            raise ValueError('Require must be required')
        if value in (None, {}, [], (), '') and not self.nullable:
            raise ValueError('Require must be not empty')

    def valid_field(self, value):
        pass


class CharField(Field):
    def valid_field(self, value):
        if not isinstance(value, str):
            raise TypeError('This value must be a string')


class ArgumentsField(Field):
    def valid_field(self, value):
        if not isinstance(value, dict):
            raise TypeError('This value must be a dict')


class EmailField(CharField):
    def valid_field(self, value):
        super().valid_field(value)
        if '@' not in value:
            raise TypeError('This value must be a email')


class PhoneField(Field):
    def valid_field(self, value):
        if not isinstance(value, (str, int)):
            raise TypeError('This value must be a number or str')
        if not str(value).startswith('7') or len(str(value)) != 11:
            raise SyntaxError('Length phone number must be 11 characters and begin with "7"')


class DateField(CharField):
    def valid_field(self, value):
        super().valid_field(value)
        try:
            self._date = datetime.datetime.strptime(value, '%d.%m.%Y').date()
        except:
            raise TypeError('Date must be string in format "DD.MM.YYYY"')


class BirthDayField(DateField):
    def valid_field(self, value):
        super().valid_field(value)
        _date_from_day = datetime.date.today() - self._date
        if _date_from_day.days < 0:
            raise ValueError('Date does not exist yet')
        _date_max = datetime.date.today() - datetime.date(datetime.date.today().year - 70,
                                                          datetime.date.today().month,
                                                          datetime.date.today().day)
        if _date_from_day.days > _date_max.days:
            raise SyntaxError('More than 70 years have passed since the date of birth')


class GenderField(Field):
    def valid_field(self, value):
        if value not in GENDERS.keys():
            raise TypeError('His field must be a integer number with the value 0, 1 or 2')


class ClientIDsField(Field):
    def valid_field(self, value):
        if not isinstance(value, list):
            raise TypeError('His field must be a list')
        if not all(isinstance(number, int) for number in value):
            raise TypeError('His list must contain integer')
        if not all(number >= 0 for number in value):
            raise ValueError('His list must contain positive integer')


class MetaClassRequest(type):
    def __new__(mcs, name, bases, dct):
        var_inst_cls = {key: dct[key] for key in dct.keys() if isinstance(dct[key], Field)}
        inst_cls = {key: dct[key] for key in dct.keys() - var_inst_cls.keys()}
        inst_cls["__inst_cls"] = var_inst_cls
        return super().__new__(mcs, name, bases, inst_cls)


class Request(metaclass=MetaClassRequest):
    def __init__(self, request={}):
        self.list_not_null_fields = []
        self.dict_err_type_value = {}
        for name_field, val_field in getattr(self, '__inst_cls').items():
            try:
                if name_field in request:
                    value = request[name_field]
                else:
                    raise ValueError('Empty value %s', name_field)
                val_field.valid_required_nullable(value)
                val_field.valid_field(value)
                setattr(self, name_field, value)
                self.list_not_null_fields.append(name_field)

            except (TypeError, SyntaxError) as err:
                self.dict_err_type_value[name_field] = err
            except ValueError as err:
                if getattr(val_field, 'required'):
                    self.dict_err_type_value[name_field] = err


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def get_operation(self, _store, list_par, context):
        col_clients = 0
        answer_get_interests = {}
        if "client_ids" in list_par:
            for client in getattr(self, 'client_ids'):
                _args = {'store': _store}
                _args['client_ids'] = client
                col_clients +=1
                answer_get_interests[str(client)] = _get_interests(*_args)
            context["nclients"] = col_clients
        else:
            self.dict_err_type_value['client_ids'] = \
                ValueError('"client_ids" should not be dusty ')
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST
        return answer_get_interests, OK


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validated_argument(self, list_not_null_fields):
        if not self.dict_err_type_value:
            if 'phone' in list_not_null_fields and \
                    'email' in list_not_null_fields:
                return True
            if 'first_name' in list_not_null_fields and \
                    'last_name' in list_not_null_fields:
                return True
            if 'gender' in list_not_null_fields and \
                    'birthday' in list_not_null_fields:
                return True
        self.dict_err_type_value['arguments'] = 'Arguments are not valid'
        return False

    def get_operation(self, _store, list_par, context):
        if not self.validated_argument(list_par):
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST
        else:
            _args = {'store': _store}
            _list_par = list_par[:]
            for val in _list_par:
                if getattr(self, val) not in (None, {}, [], (), ''):
                    _args[val] = getattr(self, val)
            context['has'] = list_par
            return {'score': _get_score(*_args)}, OK


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(
            bytes(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT, encoding='utf-8')).hexdigest()
    else:
        digest = hashlib.sha512(bytes(request.account + request.login + SALT, encoding='utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    handler = {
        "online_score": OnlineScoreRequest,
        "clients_interests": ClientsInterestsRequest
    }
    _request = MethodRequest(request['body'])
    if _request.dict_err_type_value:
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    if check_auth(_request):
        _arguments = handler[_request.method](request['body']['arguments'])
        if _arguments.dict_err_type_value:
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST
        if _request.is_admin:
            return {'score': 42}, OK
        else:
            return _arguments.get_operation(store, _arguments.list_not_null_fields, ctx)
    else:
        return ERRORS[FORBIDDEN], FORBIDDEN


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST
        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r, ensure_ascii=False).encode("utf-8"))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
