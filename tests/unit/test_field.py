import unittest
import api
from libtools import cases


class TestField(unittest.TestCase):

    @cases([None, [], {}, '', (),])
    def test_field_empty(self, string):
        field = api.Field(required=True, nullable=False)
        with self.assertRaises(ValueError):
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

    @cases(['123445', 'qwer'])
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

    @cases(['mailmail.ru'])
    def test_email_field_typeerror(self, string):
        self.field_email = api.EmailField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_email.valid_field(string)

    @cases(['mail@mail.ru', '@'])
    def est_email_field_request(self, string):
        self.field_email._value = string
        self.assertEqual(string, self.field_email._value)


class TestPhoneField(unittest.TestCase):

    @cases(['7234567890', '82345678901', '790675423121'])
    def test_phone_field_typeerror(self, string):
        self.field_phone = api.PhoneField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_phone.valid_field(string)

    @cases(['71231231212'])
    def est_phone_field_request(self, string):
        self.field_phone._value = string
        self.assertEqual(string, self.field_phone._value)


class TestDateField(unittest.TestCase):

    @cases(['xxx', '01.01.194', '01.01.19422'])
    def test_date_field_typeerror(self, string):
        self.field_date = api.DateField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_date.valid_field(string)

    @cases(['01.01.1999'])
    def est_dete_field_request(self, string):
        self.field_date._value = string
        self.assertEqual(string, self.field_date._value)


class TestBirthDayField(unittest.TestCase):

    @cases(['xxx', '01.01.1950', 1011950, 'dd.mm.YYYY'])
    def test_date_field_typeerror(self, string):
        self.field_birthday = api.BirthDayField(required=True, nullable=True)
        with self.assertRaises(api.ValidationError):
            self.field_birthday.valid_field(string)

    @cases(['01.01.2029'])
    def test_date_field_valueerror(self, string):
        self.field_birthday = api.BirthDayField(required=True, nullable=True)
        with self.assertRaises(ValueError):
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
