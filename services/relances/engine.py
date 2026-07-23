"""Moteur de relances (Phase 0) - cf. docs/Artisia_SpecFonctionnelle_2026-07-07.md section 3.4.

Calcule les relances dues (devis en attente, factures impayees) sur les paliers
J+3/J+7/J+15 et les enregistre une fois envoyees. N'appelle aucun fournisseur :
le canal d'envoi reel (email/SMS) n'est pas encore source (CLAUDE.md section 2/5).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable, Protocol

PALIERS: list[tuple[int, int]] = [(1, 3), (2, 7), (3, 15)]  # (palier, jours apres reference)
CANAL_PAR_PALIER: dict[int, str] = {1: "email", 2: "sms", 3: "email"}


@dataclass(frozen=True)
class RelanceDue:
    cible_type: str  # 'devis' | 'facture'
    cible_id: int
    artisan_id: int
    palier: int
    canal: str
    destinataire_client_id: int


class Notifier(Protocol):
    """A implementer une fois un fournisseur email/SMS source et teste."""

    def send(self, canal: str, client_id: int, message: str) -> bool: ...


def _to_date(value: str) -> date:
    return datetime.fromisoformat(value).date()


def _sequence_interrompue(conn: sqlite3.Connection, cible_type: str, cible_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM relances WHERE cible_type = ? AND cible_id = ? AND interrompue = 1 LIMIT 1",
        (cible_type, cible_id),
    ).fetchone()
    return row is not None


def _paliers_deja_envoyes(conn: sqlite3.Connection, cible_type: str, cible_id: int) -> set[int]:
    rows = conn.execute(
        "SELECT palier FROM relances WHERE cible_type = ? AND cible_id = ?",
        (cible_type, cible_id),
    ).fetchall()
    return {r[0] for r in rows}


def get_due_reminders(conn: sqlite3.Connection, today: date) -> list[RelanceDue]:
    """Devis dormants (statut='envoye') et factures impayees dont un palier est atteint."""
    due: list[RelanceDue] = []

    devis_rows = conn.execute(
        "SELECT id, artisan_id, client_id, date_envoi FROM devis WHERE statut = 'envoye'"
    ).fetchall()
    for devis_id, artisan_id, client_id, date_envoi in devis_rows:
        due.extend(
            _due_for_cible(conn, "devis", devis_id, artisan_id, client_id, _to_date(date_envoi), today)
        )

    facture_rows = conn.execute(
        "SELECT id, artisan_id, client_id, date_echeance FROM factures WHERE statut IN ('emise', 'impayee')"
    ).fetchall()
    for facture_id, artisan_id, client_id, date_echeance in facture_rows:
        due.extend(
            _due_for_cible(conn, "facture", facture_id, artisan_id, client_id, _to_date(date_echeance), today)
        )

    return due


def _due_for_cible(
    conn: sqlite3.Connection,
    cible_type: str,
    cible_id: int,
    artisan_id: int,
    client_id: int,
    reference: date,
    today: date,
) -> list[RelanceDue]:
    if _sequence_interrompue(conn, cible_type, cible_id):
        return []

    deja_envoyes = _paliers_deja_envoyes(conn, cible_type, cible_id)
    jours_ecoules = (today - reference).days

    result = []
    for palier, seuil_jours in PALIERS:
        if palier in deja_envoyes:
            continue
        if jours_ecoules >= seuil_jours:
            result.append(
                RelanceDue(
                    cible_type=cible_type,
                    cible_id=cible_id,
                    artisan_id=artisan_id,
                    palier=palier,
                    canal=CANAL_PAR_PALIER[palier],
                    destinataire_client_id=client_id,
                )
            )
    return result


def record_reminder_sent(conn: sqlite3.Connection, reminder: RelanceDue, sent_at: date) -> None:
    conn.execute(
        "INSERT INTO relances (artisan_id, cible_type, cible_id, canal, palier, envoyee_le, interrompue) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (reminder.artisan_id, reminder.cible_type, reminder.cible_id, reminder.canal, reminder.palier, sent_at.isoformat()),
    )


def _default_message(conn: sqlite3.Connection, reminder: RelanceDue) -> str:
    return f"Relance palier {reminder.palier} ({reminder.cible_type} #{reminder.cible_id})"


def run_daily_batch(
    conn: sqlite3.Connection,
    notifier: Notifier,
    today: date,
    message_builder: Callable[[sqlite3.Connection, "RelanceDue"], str] = _default_message,
) -> int:
    """Envoie toutes les relances dues via `notifier`. Retourne le nombre envoye.

    `message_builder` genere le texte reel (cf. messages.build_message pour les
    gabarits produit) - un builder generique est utilise par defaut pour ne pas
    forcer un import croise entre les deux modules.
    """
    sent = 0
    for reminder in get_due_reminders(conn, today):
        message = message_builder(conn, reminder)
        if notifier.send(reminder.canal, reminder.destinataire_client_id, message):
            record_reminder_sent(conn, reminder, today)
            sent += 1
    return sent


def average_collection_delay_days(conn: sqlite3.Connection, with_relance: bool) -> float | None:
    """Indicateur du Definition of Done (CLAUDE.md section 10) : delai moyen
    d'encaissement, factures payees ayant recu au moins une relance vs non.
    """
    rows = conn.execute(
        "SELECT id, created_at, date_paiement FROM factures WHERE statut = 'payee' AND date_paiement IS NOT NULL"
    ).fetchall()
    delays = []
    for facture_id, created_at, date_paiement in rows:
        a_recu_relance = (
            conn.execute(
                "SELECT 1 FROM relances WHERE cible_type = 'facture' AND cible_id = ? LIMIT 1",
                (facture_id,),
            ).fetchone()
            is not None
        )
        if a_recu_relance != with_relance:
            continue
        delays.append((_to_date(date_paiement) - _to_date(created_at)).days)

    return sum(delays) / len(delays) if delays else None
