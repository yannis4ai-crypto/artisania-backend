import unittest
from unittest.mock import MagicMock

from composite_notifier import CompositeNotifier


class CompositeNotifierTests(unittest.TestCase):
    def test_routes_email_to_email_notifier(self):
        email_notifier = MagicMock()
        email_notifier.send.return_value = True
        sms_notifier = MagicMock()

        notifier = CompositeNotifier(email_notifier, sms_notifier)
        result = notifier.send("email", client_id=1, message="x")

        self.assertTrue(result)
        email_notifier.send.assert_called_once_with("email", 1, "x")
        sms_notifier.send.assert_not_called()

    def test_routes_sms_to_sms_notifier(self):
        email_notifier = MagicMock()
        sms_notifier = MagicMock()
        sms_notifier.send.return_value = True

        notifier = CompositeNotifier(email_notifier, sms_notifier)
        result = notifier.send("sms", client_id=1, message="x")

        self.assertTrue(result)
        sms_notifier.send.assert_called_once_with("sms", 1, "x")
        email_notifier.send.assert_not_called()

    def test_unknown_canal_returns_false(self):
        notifier = CompositeNotifier(MagicMock(), MagicMock())
        result = notifier.send("fax", client_id=1, message="x")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
