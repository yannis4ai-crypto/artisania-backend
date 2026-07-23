"""Implementation Notifier - canal email via l'API Mailjet (Send API v3.1).

Remplace gmail_notifier.py (decision stack 7-8 juillet 2026). Canal SMS gere
par sinch_notifier.py, pas ici : send() renvoie False pour tout canal != 'email',
sans simulation.

Auth confirmee via dev.mailjet.com/email/guides/send-api-v31 (7 juillet 2026) :
HTTP Basic Auth, username = API Key, password = API Secret.
"""

from __future__ import annotations

import base64
import json
import os
import sqlite3
import urllib.error
import urllib.request

MAILJET_SEND_URL = "https://api.mailjet.com/v3.1/send"
OBJET_RELANCE = "Relance Artisia"


class MailjetNotifier:
    def __init__(
        self,
        conn: sqlite3.Connection,
        api_key: str | None = None,
        api_secret: str | None = None,
        from_email: str | None = None,
    ) -> None:
        self.conn = conn
        self.api_key = api_key or os.environ["MAILJET_API_KEY"]
        self.api_secret = api_secret or os.environ["MAILJET_API_SECRET"]
        self.from_email = from_email or os.environ.get("MAILJET_FROM_EMAIL", "relances@artisia.fr")

    def send(self, canal: str, client_id: int, message: str) -> bool:
        if canal != "email":
            return False  # canal hors perimetre de ce notifier (cf. sinch_notifier.py pour 'sms')

        row = self.conn.execute("SELECT email FROM clients WHERE id = ?", (client_id,)).fetchone()
        if row is None or not row[0]:
            return False

        payload = {
            "Messages": [
                {
                    "From": {"Email": self.from_email, "Name": "Artisia"},
                    "To": [{"Email": row[0]}],
                    "Subject": OBJET_RELANCE,
                    "TextPart": message,
                }
            ]
        }
        return self._post(payload)

    def _post(self, payload: dict) -> bool:
        credentials = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
        request = urllib.request.Request(
            MAILJET_SEND_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {credentials}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except urllib.error.URLError:
            return False
