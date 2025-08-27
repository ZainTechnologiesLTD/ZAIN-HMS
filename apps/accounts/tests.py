from django.test import TestCase


class AccountsSmokeTest(TestCase):
    def test_import(self):
        # Ensure app loads
        import apps.accounts
        self.assertTrue(True)
