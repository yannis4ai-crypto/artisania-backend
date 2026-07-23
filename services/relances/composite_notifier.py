"""Route chaque envoi vers le notifier du canal correspondant.

Necessaire depuis le passage a deux fournisseurs distincts (Mailjet pour
l'email, Sinch pour le SMS - decision stack 7-8 juillet 2026) : engine.py
n'attend qu'un seul objet `Notifier`, ce composite l'expose en delegant a
l'implementation du bon canal.
"""

from __future__ import annotations


class CompositeNotifier:
    def __init__(self, email_notifier, sms_notifier) -> None:
        self._by_canal = {"email": email_notifier, "sms": sms_notifier}

    def send(self, canal: str, client_id: int, message: str) -> bool:
        notifier = self._by_canal.get(canal)
        if notifier is None:
            return False
        return notifier.send(canal, client_id, message)
