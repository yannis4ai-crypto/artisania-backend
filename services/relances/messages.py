"""Gabarits de message des relances - ton chaleureux, jamais agressif
(cf. docs/Artisia_SpecFonctionnelle_2026-07-07.md section 3.4 : "calibrer pour
ne pas heurter la relation client"). Textes de depart a affiner avec un
artisan pilote reel, pas des textes definitifs.
"""

from __future__ import annotations

import sqlite3

from engine import RelanceDue

DEVIS_TEMPLATES: dict[int, str] = {
    1: (
        "Bonjour {nom}, petit rappel : votre devis n°{id} d'un montant de {montant:.2f} € "
        "est toujours en attente de votre retour. N'hésitez pas à nous contacter si vous avez des questions."
    ),
    2: (
        "Bonjour {nom}, nous n'avons pas encore eu de retour concernant votre devis n°{id} "
        "({montant:.2f} €). Souhaitez-vous qu'on en discute ensemble ?"
    ),
    3: (
        "Bonjour {nom}, votre devis n°{id} ({montant:.2f} €) est toujours sans réponse. "
        "Dites-nous si le projet n'est plus d'actualité, sinon nous restons à votre disposition."
    ),
}

FACTURE_TEMPLATES: dict[int, str] = {
    1: (
        "Bonjour {nom}, petit rappel amical : la facture n°{id} d'un montant de {montant:.2f} € "
        "est en attente de règlement. Merci de votre retour."
    ),
    2: (
        "Bonjour {nom}, nous n'avons pas encore reçu le paiement de la facture n°{id} "
        "({montant:.2f} €). Pourriez-vous nous indiquer où cela en est ?"
    ),
    3: (
        "Bonjour {nom}, la facture n°{id} ({montant:.2f} €) reste impayée. "
        "Merci de régulariser rapidement ou de nous contacter pour en discuter."
    ),
}

_TABLE_BY_CIBLE: dict[str, tuple[str, dict[int, str]]] = {
    "devis": ("devis", DEVIS_TEMPLATES),
    "facture": ("factures", FACTURE_TEMPLATES),
}


def _client_nom(conn: sqlite3.Connection, client_id: int) -> str:
    row = conn.execute("SELECT nom FROM clients WHERE id = ?", (client_id,)).fetchone()
    return row[0] if row else "Client"


def build_message(conn: sqlite3.Connection, reminder: RelanceDue) -> str:
    table_name, templates = _TABLE_BY_CIBLE[reminder.cible_type]
    row = conn.execute(f"SELECT montant_total FROM {table_name} WHERE id = ?", (reminder.cible_id,)).fetchone()
    montant = row[0] if row else 0.0
    nom = _client_nom(conn, reminder.destinataire_client_id)
    return templates[reminder.palier].format(nom=nom, id=reminder.cible_id, montant=montant)
