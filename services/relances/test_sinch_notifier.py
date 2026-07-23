import json
import sqlite3
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from sinch_notifier import SinchNotifier

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        "INSERT INTO artisans (id, nom_entreprise, metier, email, created_at) "
        "VALUES (1, 'Plomberie Test', 'plombier', 'a@test.fr', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO clients (id, artisan_id, nom, telephone, created_at) "
        "VALUES (1, 1, 'Client Test', '+33600000000', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO clients (id, artisan_id, nom, created_at) "
        "VALUES (2, 1, 'Client Sans Telephone', '2026-01-01')"
    )
    return conn


def make_notifier(conn: sqlite3.Connection) -> SinchNotifier:
    return SinchNotifier(
        conn,
        api_key="service-plan-123",
        api_secret="token123",
        sender="ArtisiaSMS",
        region="eu",
    )


class SinchNotifierTests(unittest.TestCase):
    @patch("sinch_notifier.urllib.request.urlopen")
    def test_sends_sms_successfully(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        notifier = make_notifier(make_conn())
        result = notifier.send("sms", client_id=1, message="Votre facture est en attente.")

        self.assertTrue(result)
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(
            request.full_url,
            "https://eu.sms.api.sinch.com/xms/v1/service-plan-123/batches",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer token123")
        body = json.loads(request.data)
        self.assertEqual(body["to"], ["+33600000000"])
        self.assertEqual(body["from"], "ArtisiaSMS")

    @patch("sinch_notifier.urllib.request.urlopen")
    def test_api_failure_returns_false(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("boom")

        notifier = make_notifier(make_conn())
        result = notifier.send("sms", client_id=1, message="x")

        self.assertFalse(result)

    @patch("sinch_notifier.urllib.request.urlopen")
    def test_client_without_telephone_returns_false(self, mock_urlopen):
        notifier = make_notifier(make_conn())
        result = notifier.send("sms", client_id=2, message="x")

        self.assertFalse(result)
        mock_urlopen.assert_not_called()

    @patch("sinch_notifier.urllib.request.urlopen")
    def test_email_canal_returns_false_without_calling_api(self, mock_urlopen):
        notifier = make_notifier(make_conn())
        result = notifier.send("email", client_id=1, message="x")

        self.assertFalse(result)
        mock_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
