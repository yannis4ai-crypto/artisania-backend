import sqlite3
import unittest
from datetime import date
from pathlib import Path

from engine import (
    average_collection_delay_days,
    get_due_reminders,
    record_reminder_sent,
    run_daily_batch,
)

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"


class FakeNotifier:
    def __init__(self, should_succeed: bool = True):
        self.sent: list[tuple[str, int, str]] = []
        self.should_succeed = should_succeed

    def send(self, canal: str, client_id: int, message: str) -> bool:
        self.sent.append((canal, client_id, message))
        return self.should_succeed


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        "INSERT INTO artisans (id, nom_entreprise, metier, email, created_at) "
        "VALUES (1, 'Plomberie Test', 'plombier', 'a@test.fr', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO clients (id, artisan_id, nom, created_at) VALUES (1, 1, 'Client Test', '2026-01-01')"
    )
    return conn


class RelanceSequencingTests(unittest.TestCase):
    def test_no_reminder_before_j3(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, date_envoi, created_at, updated_at) "
            "VALUES (1, 1, 1, 'envoye', 500, 1, '2026-02-01', '2026-02-01', '2026-02-01')"
        )
        due = get_due_reminders(conn, today=date(2026, 2, 2))  # J+1
        self.assertEqual(due, [])

    def test_reminder_due_at_j3(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, date_envoi, created_at, updated_at) "
            "VALUES (1, 1, 1, 'envoye', 500, 1, '2026-02-01', '2026-02-01', '2026-02-01')"
        )
        due = get_due_reminders(conn, today=date(2026, 2, 4))  # J+3
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].palier, 1)
        self.assertEqual(due[0].canal, "email")

    def test_no_duplicate_after_sent(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, date_envoi, created_at, updated_at) "
            "VALUES (1, 1, 1, 'envoye', 500, 1, '2026-02-01', '2026-02-01', '2026-02-01')"
        )
        notifier = FakeNotifier()
        sent_day1 = run_daily_batch(conn, notifier, today=date(2026, 2, 4))
        sent_day2 = run_daily_batch(conn, notifier, today=date(2026, 2, 4))
        self.assertEqual(sent_day1, 1)
        self.assertEqual(sent_day2, 0)

    def test_all_three_paliers_reached_over_time(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, date_envoi, created_at, updated_at) "
            "VALUES (1, 1, 1, 'envoye', 500, 1, '2026-02-01', '2026-02-01', '2026-02-01')"
        )
        notifier = FakeNotifier()
        run_daily_batch(conn, notifier, today=date(2026, 2, 4))   # J+3 -> palier 1
        run_daily_batch(conn, notifier, today=date(2026, 2, 8))   # J+7 -> palier 2
        run_daily_batch(conn, notifier, today=date(2026, 2, 16))  # J+15 -> palier 3
        paliers_envoyes = [row[0] for row in conn.execute("SELECT palier FROM relances ORDER BY palier")]
        self.assertEqual(paliers_envoyes, [1, 2, 3])
        self.assertEqual([c for c, _, _ in notifier.sent], ["email", "sms", "email"])

    def test_interruption_stops_sequence(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, date_envoi, created_at, updated_at) "
            "VALUES (1, 1, 1, 'envoye', 500, 1, '2026-02-01', '2026-02-01', '2026-02-01')"
        )
        conn.execute(
            "INSERT INTO relances (artisan_id, cible_type, cible_id, canal, palier, envoyee_le, interrompue) "
            "VALUES (1, 'devis', 1, 'email', 1, '2026-02-04', 1)"
        )
        due = get_due_reminders(conn, today=date(2026, 2, 16))
        self.assertEqual(due, [])

    def test_facture_impayee_uses_echeance_as_reference(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO factures (id, artisan_id, client_id, statut, montant_total, date_echeance, created_at, updated_at) "
            "VALUES (1, 1, 1, 'impayee', 800, '2026-03-01', '2026-02-01', '2026-02-01')"
        )
        # echeance + 7 jours, aucune relance encore envoyee -> paliers 1 (J+3) et 2 (J+7) dus a la fois
        due = get_due_reminders(conn, today=date(2026, 3, 8))
        self.assertEqual({r.palier for r in due}, {1, 2})
        self.assertTrue(all(r.cible_type == "facture" for r in due))

    def test_average_collection_delay(self):
        conn = make_conn()
        conn.execute(
            "INSERT INTO factures (id, artisan_id, client_id, statut, montant_total, date_echeance, date_paiement, created_at, updated_at) "
            "VALUES (1, 1, 1, 'payee', 800, '2026-03-01', '2026-03-20', '2026-02-01', '2026-03-20')"
        )
        conn.execute(
            "INSERT INTO relances (artisan_id, cible_type, cible_id, canal, palier, envoyee_le, interrompue) "
            "VALUES (1, 'facture', 1, 'email', 1, '2026-03-04', 0)"
        )
        with_relance = average_collection_delay_days(conn, with_relance=True)
        without_relance = average_collection_delay_days(conn, with_relance=False)
        self.assertEqual(with_relance, 47.0)  # 2026-02-01 -> 2026-03-20
        self.assertIsNone(without_relance)


if __name__ == "__main__":
    unittest.main()
