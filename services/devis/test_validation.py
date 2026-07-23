import sqlite3
import unittest
from datetime import date
from pathlib import Path

from validation import DevisNonValideError, DevisStatutInvalideError, mark_validated, send_devis

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"


def make_conn(valide_par_artisan: int = 0, statut: str = "brouillon") -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        "INSERT INTO artisans (id, nom_entreprise, metier, email, created_at) "
        "VALUES (1, 'Plomberie Test', 'plombier', 'a@test.fr', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO clients (id, artisan_id, nom, created_at) VALUES (1, 1, 'Client Test', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, created_at, updated_at) "
        "VALUES (1, 1, 1, ?, 500, ?, '2026-01-01', '2026-01-01')",
        (statut, valide_par_artisan),
    )
    return conn


class DevisValidationTests(unittest.TestCase):
    def test_send_blocked_when_not_validated(self):
        conn = make_conn(valide_par_artisan=0)
        with self.assertRaises(DevisNonValideError):
            send_devis(conn, devis_id=1, sent_on=date(2026, 2, 1))
        statut = conn.execute("SELECT statut FROM devis WHERE id = 1").fetchone()[0]
        self.assertEqual(statut, "brouillon")

    def test_send_succeeds_after_validation(self):
        conn = make_conn(valide_par_artisan=0)
        mark_validated(conn, devis_id=1, validated_on=date(2026, 1, 15))
        send_devis(conn, devis_id=1, sent_on=date(2026, 2, 1))
        statut, date_envoi = conn.execute(
            "SELECT statut, date_envoi FROM devis WHERE id = 1"
        ).fetchone()
        self.assertEqual(statut, "envoye")
        self.assertEqual(date_envoi, "2026-02-01")

    def test_send_blocked_when_not_brouillon(self):
        conn = make_conn(valide_par_artisan=1, statut="envoye")
        with self.assertRaises(DevisStatutInvalideError):
            send_devis(conn, devis_id=1, sent_on=date(2026, 2, 1))

    def test_send_unknown_devis_raises(self):
        conn = make_conn()
        with self.assertRaises(ValueError):
            send_devis(conn, devis_id=999, sent_on=date(2026, 2, 1))


if __name__ == "__main__":
    unittest.main()
