import unittest

from app.schemas.whatsapp import WhatsAppTemplateRequestSimple
from app.utils.utils import PhoneNumberValidationError, normalize_phone_number


class NormalizePhoneNumberTests(unittest.TestCase):
    def test_removes_common_phone_separators(self):
        self.assertEqual(normalize_phone_number("+52 (55) 1234-5678"), "5215512345678")

    def test_accepts_international_access_prefix(self):
        self.assertEqual(normalize_phone_number("0052 55 1234 5678"), "5215512345678")

    def test_adds_default_country_code_to_local_mexican_number(self):
        self.assertEqual(normalize_phone_number("55 1234 5678"), "5215512345678")

    def test_rejects_letters_and_invalid_lengths(self):
        with self.assertRaises(PhoneNumberValidationError):
            normalize_phone_number("55-ABCD-5678")
        with self.assertRaises(PhoneNumberValidationError):
            normalize_phone_number("123")

    def test_template_request_is_normalized_at_the_api_boundary(self):
        payload = WhatsAppTemplateRequestSimple(
            to="+52 (55) 1234-5678",
            template_name="hello_world",
        )
        self.assertEqual(payload.to, "5215512345678")
