import unittest

from access import allowed_user_ids, is_authorized


class AccessTests(unittest.TestCase):
    def test_unset_or_empty_denies_everyone(self):
        self.assertFalse(is_authorized(123, ""))
        self.assertFalse(is_authorized(123, "   ,  "))
        self.assertEqual(allowed_user_ids(""), set())

    def test_only_listed_ids_allowed(self):
        self.assertTrue(is_authorized(123, "123"))
        self.assertTrue(is_authorized(456, "123, 456"))
        self.assertFalse(is_authorized(789, "123,456"))

    def test_garbage_ignored_and_none_denied(self):
        self.assertEqual(allowed_user_ids("abc,12x,77"), {77})
        self.assertFalse(is_authorized(None, "123"))

    def test_env_is_used_by_default(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"ALLOWED_USER_IDS": "5"}):
            self.assertTrue(is_authorized(5))
            self.assertFalse(is_authorized(6))
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_authorized(5))


if __name__ == "__main__":
    unittest.main()
