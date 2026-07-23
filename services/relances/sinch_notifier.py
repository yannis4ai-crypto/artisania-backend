"""Implementation Notifier - canal sms via l'API Sinch (SMS API, batches).

Nouveau canal (decision stack 7-8 juillet 2026), integration separee de
mailjet_notifier.py. Canal email non gere ici : send() renvoie False pour
tout canal != 'sms', sans simulation.

Auth confirmee via developers.sinch.com/docs/sms (7 juillet 2026) : Bearer
token dans le header Authorization, service plan ID dans l'URL. Mapping des
variables d'environnement de ce projet -> concepts Sinch :
  SINCH_API_KEY    -> Service Plan ID (chemin de l'URL)
  SINCH_API_SECRET -> API Token (Bearer)
  SINCH_SENDER     -> numero expediteur Sinch

Region par defaut EU (Irlande/Suede, cf. doc Sinch) puisque la cible est
francaise - `SINCH_REGION` permet de basculer sur 'us'/'au'/'br'/'ca' si besoin.
"""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request

SINCH_SMS_URL_TEMPLATE = "https://{region}.sms.api.sinch.com/xms/v1/{service_plan_id}/batches"


class SinchNotifier:
    def __init__(
        self,
        conn: sqlite3.Connection,
        api_key: str | None = None,
        api_secret: str | None = None,
        sender: str | None = None,
        region: str | None = None,
    ) -> None:
        self.conn = conn
        self.api_key = api_key or os.environ["SINCH_API_KEY"]
        self.api_secret = api_secret or os.environ["SINCH_API_SECRET"]
        self.sender = sender or os.environ["SINCH_SENDER"]
        self.region = region or os.environ.get("SINCH_REGION", "eu")

    def send(self, canal: str, client_id: int, message: str) -> bool:
        if canal != "sms":
            return False  # canal hors perimetre de ce notifier (cf. mailjet_notifier.py pour 'email')

        row = self.conn.execute("SELECT telephone FROM clients WHERE id = ?", (client_id,)).fetchone()
        if row is None or not row[0]:
            return False

        payload = {"from": self.sender, "to": [row[0]], "body": message}
        return self._post(payload)

    def _post(self, payload: dict) -> bool:
        url = SINCH_SMS_URL_TEMPLATE.format(region=self.region, service_plan_id=self.api_key)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_secret}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except urllib.error.URLError:
            return False
