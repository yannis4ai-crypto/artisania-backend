import json
import sqlite3
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from mailjet_notifier import MailjetNotifier

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        "INSERT INTO artisans (id, nom_entreprise, metier, email, created_at) "
        "VALUES (1, 'Plomberie Test', 'plombier', 'a@test.fr', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO clients (id, artisan_id, nom, email, created_at) "
        "VALUES (1, 1, 'Client Test', 'client@test.fr', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO clients (id, artisan_id, nom, created_at) "
        "VALUES (2, 1, 'Client Sans Email', '2026-01-01')"
    )
    return conn


def make_notifier(conn: sqlite3.Connection) -> MailjetNotifier:
    return MailjetNotifier(conn, api_key="key123", api_secret="secret123", from_email="relances@artisia.fr")


class MailjetNotifierTests(unittest.TestCase):
    @patch("mailjet_notifier.urllib.request.urlopen")
    def test_sends_email_successfully(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        notifier = make_notifier(make_conn())
        result = notifier.send("email", client_id=1, message="Votre devis est en attente.")

        self.assertTrue(result)
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.mailjet.com/v3.1/send")
        body = json.loads(request.data)
        self.assertEqual(body["Messages"][0]["To"][0]["Email"], "client@test.fr")
        self.assertEqual(body["Messages"][0]["From"]["Email"], "relances@artisia.fr")

    @patch("mailjet_notifier.urllib.request.urlopen")
    def test_api_failure_returns_false(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("boom")

        notifier = make_notifier(make_conn())
        result = notifier.send("email", client_id=1, message="Votre devis est en attente.")

        self.assertFalse(result)

    @patch("mailjet_notifier.urllib.request.urlopen")
    def test_client_without_email_returns_false(self, mock_urlopen):
        notifier = make_notifier(make_conn())
        result = notifier.send("email", client_id=2, message="Votre devis est en attente.")

        self.assertFalse(result)
        mock_urlopen.assert_not_called()

    @patch("mailjet_notifier.urllib.request.urlopen")
    def test_sms_canal_returns_false_without_calling_api(self, mock_urlopen):
        notifier = make_notifier(make_conn())
        result = notifier.send("sms", client_id=1, message="x")

        self.assertFalse(result)
        mock_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
