"""CLI pour executer le batch quotidien de relances - a brancher sur un cron.

Usage :
    python3 cli.py --db /chemin/vers/artisia.db

Necessite MAILJET_API_KEY/MAILJET_API_SECRET (email) et SINCH_API_KEY/
SINCH_API_SECRET/SINCH_SENDER (SMS) dans l'environnement (cf. .env.example).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date
from pathlib import Path

from composite_notifier import CompositeNotifier
from engine import run_daily_batch
from mailjet_notifier import MailjetNotifier
from messages import build_message
from sinch_notifier import SinchNotifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch quotidien de relances Artisia")
    parser.add_argument("--db", required=True, help="Chemin vers la base SQLite (schema deja applique)")
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Base introuvable : {db_path} (appliquer data/schema.sql au prealable)", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    try:
        notifier = CompositeNotifier(MailjetNotifier(conn), SinchNotifier(conn))
        sent = run_daily_batch(conn, notifier, today=date.today(), message_builder=build_message)
        conn.commit()
        print(f"{sent} relance(s) envoyee(s).")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
