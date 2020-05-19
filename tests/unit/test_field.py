import unittest
import api
from libtools import cases


class TestField(unittest.TestCase):

    @cases([None, [], {}, '', (),])
    def test_field_empty(self, string):
        field = api.Field(required=True, nullable=False)
        with self.assertRaises(api.ValidationError):
            field.valid_required_nullable(string)

    @cases([1, 'qwer'])
    def test_field_request(self, string):
        field = api.Field(required=True, nullable=True)
        field._value = string
        self.assertEqual(string, field._value)


class TestCharField(unittest.TestCase):

    @cases([0, None, [], {}, [1, 2, 3, 4], [0], {0}, {'123'}, ['123'],])
    def test_charfield_typeerror(self, string):
        field_char = api.CharField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            field_char.valid_field(string)

    @cases(['123445', 'qwer', '@#$%^&&*(!)?/', 'фыва'])
    def test_charfield_request(self, string):
        field = api.CharField(required=True, nullable=True)
        field._value = string
        self.assertEqual(string, field._value)


class TestArgumentsField(unittest.TestCase):

    @cases([0, None, [], [1, 2, 3, 4], [0], {0}, {'123'}, ['123']])
    def test_argumentsfield_typeerror(self, string):
        field_arg = api.ArgumentsField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            field_arg.valid_field(string)

    @cases({'1': '1234sdf'})
    def test_argumentsfield_request(self, string):
        field = api.ArgumentsField(required=True, nullable=True)
        field._value = string
        c = field._value
        self.assertEqual(string, field._value)


class TestEmailField(unittest.TestCase):

    @cases(['mailmail.ru@', 'mail.ru', '@mail.ru', 'mail@mail@ru', 'mail@', '@', 'mail.mail@mail.ruru'])
    def test_email_field_typeerror(self, string):
        self.field_email = api.EmailField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_email.valid_field(string)

    @cases(['mail@mail.ru', 'mail.mail@mail.org',])
    def est_email_field_request(self, string):
        self.field_email._value = string
        self.assertEqual(string, self.field_email._value)


class TestPhoneField(unittest.TestCase):

    @cases(['7234567890', '82345678901', '790675423121',
            '+71231231212', '-71231231212', '+7123123121' ])
    def test_phone_field_typeerror(self, string):
        self.field_phone = api.PhoneField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_phone.valid_field(string)

    @cases(['71231231212'])
    def est_phone_field_request(self, string):
        self.field_phone._value = string
        self.assertEqual(string, self.field_phone._value)


class TestDateField(unittest.TestCase):

    @cases(['abc', 'abcd', 'abcde', 'abcdef', 11011999,
            '1999.24.12', '1999.12.24', '12.1999.24', '24.1999.12'
            'dd.mm.YYYY', 'MM.dd.YYYY', 'YYYY.mm.dd', 'dd.mm.YY',
            '01.12.20001', '001.12.2001', '01.001.2001', '01.12.201'])
    def test_date_field_typeerror(self, string):
        self.field_date = api.DateField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_date.valid_field(string)

    @cases(['01.01.1999', '01.01.1950', '01.01.2050'])
    def est_dete_field_request(self, string):
        self.field_date._value = string
        self.assertEqual(string, self.field_date._value)


class TestBirthDayField(unittest.TestCase):

    @cases(['abc', 'abcd', 'abcde', 'abcdef',
            11011999,
            '1999.24.12', '1999.12.24', '12.1999.24', '24.1999.12'
            'dd.mm.YYYY', 'MM.dd.YYYY', 'YYYY.mm.dd', 'dd.mm.YY',
            '01.12.20001', '001.12.2001', '01.001.2001'])
    def test_date_field_typeerror(self, string):
        self.field_birthday = api.BirthDayField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_birthday.valid_field(string)

    @cases(['01.01.2029', '01.01.1950'])
    def test_date_field_valueerror(self, string):
        self.field_birthday = api.BirthDayField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_birthday.valid_field(string)

    @cases(['01.01.1999'])
    def est_dete_field_request(self, string):
        self.field_birthday._value = string
        self.assertEqual(string, self.field_birthday._value)


class TestGenderField(unittest.TestCase):

    @cases([3, '1', 'male'])
    def test_gender_field_typeerror(self, string):
        self.field_gender = api.GenderField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_gender.valid_field(string)

    @cases([1, api.GENDERS[1]])
    def est_gender_field_request(self, string):
        self.field_gender._value = string
        self.assertEqual(string, self.field_gender._value)


class ClientIDsField(unittest.TestCase):

    @cases([['1', '2', '3'], '1'])
    def test_client_ids_field_typeerror(self, string):
        self.field_id = api.ClientIDsField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_id.valid_field(string)

    @cases([[1, 2, 3, 4, 5]])
    def est_client_ids_field_request(self, string):
        self.field_id._value = string
        self.assertEqual(string, self.field_id._value)


if __name__ == "__main__":
    unittest.main()
