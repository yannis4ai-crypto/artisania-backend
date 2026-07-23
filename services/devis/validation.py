"""Flux minimal de validation humaine avant envoi d'un devis.

Garde-fou spec (docs/Artisia_SpecFonctionnelle_2026-07-07.md section 3.3) :
un devis genere doit toujours etre relu et valide par l'artisan avant envoi -
pas d'autonomie totale, pas de sur-promesse. Le champ `devis.valide_par_artisan`
existait deja dans le schema mais rien ne l'exploitait ; ce module bloque
l'envoi tant qu'il n'est pas passe a 1.
"""

from __future__ import annotations

import sqlite3
from datetime import date


class DevisNonValideError(Exception):
    """Leve quand on tente d'envoyer un devis non relu/valide par l'artisan."""


class DevisStatutInvalideError(Exception):
    """Leve quand on tente d'envoyer un devis qui n'est pas au statut 'brouillon'."""


def mark_validated(conn: sqlite3.Connection, devis_id: int, validated_on: date | None = None) -> None:
    """L'artisan relit et valide le devis (prix, mentions legales, TVA - spec 3.3)."""
    conn.execute(
        "UPDATE devis SET valide_par_artisan = 1, updated_at = ? WHERE id = ?",
        ((validated_on or date.today()).isoformat(), devis_id),
    )


def send_devis(conn: sqlite3.Connection, devis_id: int, sent_on: date | None = None) -> None:
    """Passe le devis en statut 'envoye'. Refuse si non valide ou pas en brouillon."""
    row = conn.execute(
        "SELECT valide_par_artisan, statut FROM devis WHERE id = ?", (devis_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"devis {devis_id} introuvable")

    valide_par_artisan, statut = row
    if not valide_par_artisan:
        raise DevisNonValideError(
            f"devis {devis_id} non valide par l'artisan - envoi bloque (cf. spec section 3.3)"
        )
    if statut != "brouillon":
        raise DevisStatutInvalideError(
            f"devis {devis_id} au statut '{statut}' - l'envoi n'est possible que depuis 'brouillon'"
        )

    sent_on = sent_on or date.today()
    conn.execute(
        "UPDATE devis SET statut = 'envoye', date_envoi = ?, updated_at = ? WHERE id = ?",
        (sent_on.isoformat(), sent_on.isoformat(), devis_id),
    )
