"""Orchestration cron — Python direct, pas de n8n (cf CLAUDE.md §4)."""

import argparse
import asyncio


async def _run_relances() -> None:
    # TODO : porter le moteur de relances existant (cf CLAUDE.md §6 —
    # 11/11 tests passants dans l'environnement source, pas encore commité ici).
    raise NotImplementedError("Moteur de relances à porter depuis l'environnement existant")


COMMANDS = {"relances": _run_relances}


def main() -> None:
    parser = argparse.ArgumentParser(description="Cron Artisania")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args()
    asyncio.run(COMMANDS[args.command]())


if __name__ == "__main__":
    main()
