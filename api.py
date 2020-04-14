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


class Field(object):
    def __get__(self, instance, owner):
        return self._value.get(instance, self._value)

    def __set__(self, instance, value):
        if value is None and self.required:
            raise ValueError('Require must be required')
        if value in (None, {}, [], (), '') and self.nullable:
            print('Require must be not empty')
            raise ValueError('Require must be not empty')
        self._value[instance] = value
        self.valid_field(value)

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self._value = WeakKeyDictionary()

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
        if not str(value).startswith('7') and len(str(value)) != 11:
            raise ValueError('Length phone number must be 11 characters and begin with "7"')


class DateField(CharField):
    def valid_field(self, value):
        super().valid_field(value)
        try:
            self._date = datetime.datetime.strptime(value, '%d.%m.%Y').date()
        except:
            raise ValueError('Date must be string in format "DD.MM.YYYY"')


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
            raise ValueError('More than 70 years have passed since the date of birth')


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
        if not all(number > 0 for number in value):
            raise ValueError('His list must contain positive integer')


class MetaClassRequest(type):
    def __new__(mcs, name, bases, dct):
        var_inst_cls = {key: dct[key] for key in dct.keys() if isinstance(dct[key], Field)}
        inst_cls = {key: dct[key] for key in dct.keys() - var_inst_cls.keys()}
        inst_cls["__inst_cls"] = var_inst_cls
        return super().__new__(mcs, name, bases, inst_cls)


class Request(metaclass=MetaClassRequest):
    def __init__(self, request):
        self.request = {} if not request else request


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


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
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    handler = {
        "online_score": 'OnlineScoreRequest',
        "clients_interests": 'ClientsInterestsRequest'
    }

    code = 404

    return response, code


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
        print('headers is ', (self.headers.__hash__()))
        print(self.headers)

        print('My print', context)
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            print(data_string)
            request = json.loads(data_string)
            print(request)
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
        print("---TEST---", context)
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
