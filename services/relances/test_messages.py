import sqlite3
import unittest
from pathlib import Path

from engine import RelanceDue
from messages import build_message

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
        "VALUES (1, 1, 'Mme Martin', 'martin@test.fr', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO devis (id, artisan_id, client_id, statut, montant_total, valide_par_artisan, date_envoi, created_at, updated_at) "
        "VALUES (1, 1, 1, 'envoye', 1234.5, 1, '2026-02-01', '2026-02-01', '2026-02-01')"
    )
    conn.execute(
        "INSERT INTO factures (id, artisan_id, client_id, statut, montant_total, date_echeance, created_at, updated_at) "
        "VALUES (1, 1, 1, 'impayee', 800, '2026-03-01', '2026-02-01', '2026-02-01')"
    )
    return conn


class MessageTemplateTests(unittest.TestCase):
    def test_devis_palier1_contains_client_and_montant(self):
        conn = make_conn()
        reminder = RelanceDue("devis", 1, 1, 1, "email", 1)
        message = build_message(conn, reminder)
        self.assertIn("Mme Martin", message)
        self.assertIn("1234.50", message)
        self.assertIn("devis n°1", message)

    def test_facture_palier2_uses_facture_template(self):
        conn = make_conn()
        reminder = RelanceDue("facture", 1, 1, 2, "sms", 1)
        message = build_message(conn, reminder)
        self.assertIn("paiement de la facture n°1", message)
        self.assertIn("800.00", message)

    def test_all_paliers_have_a_template_for_both_cibles(self):
        conn = make_conn()
        for cible_type, cible_id in (("devis", 1), ("facture", 1)):
            for palier in (1, 2, 3):
                reminder = RelanceDue(cible_type, cible_id, 1, palier, "email", 1)
                message = build_message(conn, reminder)
                self.assertTrue(message)


if __name__ == "__main__":
    unittest.main()
