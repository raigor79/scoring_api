#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import logging.config
import hashlib
import uuid
from scoring import get_score, get_interests
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler

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
DEFAULT_CONFIG_FILE_NAME = 'score_api.cfg'


def _get_score(store=0, phone=None, email=None, birthday=None,
               gender=None, first_name=None, last_name=None):
    return get_score(store, phone, email, birthday, gender, first_name, last_name)


def _get_interests(store=0, cid=0):
    return get_interests(store, cid)


class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Field(object):
    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, value):
        self.valid_required_nullable(value)
        self.valid_field(value)
        self._value = value

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self._value = None

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
            raise ValidationError('This value must be a string')


class ArgumentsField(Field):
    def valid_field(self, value):
        if not isinstance(value, dict):
            raise ValidationError('This value must be a dict')


class EmailField(CharField):
    def valid_field(self, value):
        super().valid_field(value)
        if '@' not in value:
            raise ValidationError('This value must be a email')


class PhoneField(Field):
    def valid_field(self, value):
        if not isinstance(value, (str, int)):
            raise ValidationError('This value must be a number or str')
        if not str(value).startswith('7') or len(str(value)) != 11:
            raise ValidationError('Length phone number must be 11 characters and begin with "7"')


class DateField(CharField):
    def valid_field(self, value):
        super().valid_field(value)
        try:
            self.date = datetime.datetime.strptime(value, '%d.%m.%Y').date()
        except:
            raise ValidationError('Date must be string in format "DD.MM.YYYY"')


class BirthDayField(DateField):
    def valid_field(self, value):
        super().valid_field(value)
        date_from_day = datetime.date.today() - self.date
        if date_from_day.days < 0:
            raise ValueError('Date does not exist yet')
        _date_max = datetime.date.today() - datetime.date(datetime.date.today().year - 70,
                                                          datetime.date.today().month,
                                                          datetime.date.today().day)
        if date_from_day.days > _date_max.days:
            raise ValidationError('More than 70 years have passed since the date of birth')


class GenderField(Field):
    def valid_field(self, value):
        if value not in GENDERS.keys():
            raise ValidationError('His field must be a integer number with the value 0, 1 or 2')


class ClientIDsField(Field):
    def valid_field(self, value):
        if not isinstance(value, list):
            raise ValidationError('His field must be a list')
        if not all(isinstance(number, int) for number in value):
            raise ValidationError('His list must contain integer')
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
            except ValidationError as err:
                self.dict_err_type_value[name_field] = err.args[0]
            except ValueError as err:
                if getattr(val_field, 'required'):
                    self.dict_err_type_value[name_field] = err.args[0]


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


def online_score_request(store, request, context):
    score_request = OnlineScoreRequest(request)
    if score_request.dict_err_type_value:
        return score_request.dict_err_type_value, INVALID_REQUEST
    list_par = score_request.list_not_null_fields
    if not score_request.validated_argument(list_par):
        return score_request.dict_err_type_value, INVALID_REQUEST
    else:
        args = {'store': store}
        _list_par = list_par[:]
        for val in _list_par:
            if getattr(score_request, val) not in (None, {}, [], (), ''):
                args[val] = getattr(score_request, val)
        context['has'] = list_par
        return {'score': _get_score(*args)}, OK


def clients_interests_request(store, request, context):
    interest_request = ClientsInterestsRequest(request)
    if interest_request.dict_err_type_value:
        return interest_request.dict_err_type_value, INVALID_REQUEST
    list_par = interest_request.list_not_null_fields
    col_clients = 0
    answer_get_interests = {}
    if "client_ids" in list_par:
        for client in getattr(interest_request, 'client_ids'):
            args = {'store': store}
            args['client_ids'] = client
            col_clients += 1
            answer_get_interests[str(client)] = _get_interests(*args)
        context["nclients"] = col_clients
    else:
        interest_request.dict_err_type_value['client_ids'] = \
            ValueError('"client_ids" should not be dusty ').args[0]
        return interest_request.dict_err_type_value, INVALID_REQUEST
    return answer_get_interests, OK


def method_handler(request, ctx, store):
    response, code = None, None
    handler = {
        "online_score": online_score_request,
        "clients_interests": clients_interests_request
    }
    request_body = MethodRequest(request['body'])
    if request_body.dict_err_type_value:
        return request_body.dict_err_type_value, INVALID_REQUEST
    if check_auth(request_body):
        if request_body.is_admin:
            return {'score': 42}, OK
        else:
            return handler[request_body.method](store, request['body']['arguments'], ctx)
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
            logger.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logger.exception("Unexpected error: %s" % e)
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
        logger.info(context)
        self.wfile.write(json.dumps(r, ensure_ascii=False).encode("utf-8"))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-c", "--config",
                  action="store",
                  help="file config must are *.cfg",
                  default=DEFAULT_CONFIG_FILE_NAME)
    (opts, args) = op.parse_args()
    try:
        logging.config.fileConfig(opts.config)
        logger = logging.getLogger('info')
    except:
        logger = logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logger.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Script the script was interrupted by clicking Ctrl+C')
    except Exception as err:
        logger.exception(err)
    server.server_close()

