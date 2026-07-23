import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"
CLI_PATH = Path(__file__).resolve().parent / "cli.py"


class CliTests(unittest.TestCase):
    def test_runs_with_no_reminders_due(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "artisia.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(SCHEMA_PATH.read_text())
            conn.close()

            env = {
                **os.environ,
                "MAILJET_API_KEY": "key123",
                "MAILJET_API_SECRET": "secret123",
                "SINCH_API_KEY": "service-plan-123",
                "SINCH_API_SECRET": "token123",
                "SINCH_SENDER": "ArtisiaSMS",
            }
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "--db", str(db_path)],
                cwd=CLI_PATH.parent,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("0 relance(s) envoyee(s).", result.stdout)

    def test_missing_db_fails_cleanly(self):
        env = {**os.environ, "GMAIL_ADDRESS": "bot@artisia.test", "GMAIL_APP_PASSWORD": "x"}
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "--db", "/tmp/does-not-exist-artisia.db"],
            cwd=CLI_PATH.parent,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("introuvable", result.stderr)


if __name__ == "__main__":
    unittest.main()
