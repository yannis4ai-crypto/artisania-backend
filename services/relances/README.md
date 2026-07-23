# Relances (Phase 0)

Sequences email/SMS automatiques sur devis dormants et factures impayees.
Cf. `docs/Artisia_SpecFonctionnelle_2026-07-07.md` section 3.4, paliers J+3/J+7/J+15.

Schema de donnees : `data/schema.sql` (tables `devis`, `factures`, `relances`).

- **Email** : `mailjet_notifier.py` - API Mailjet (Send API v3.1, Basic Auth).
- **SMS** : `sinch_notifier.py` - API Sinch (SMS API, region EU par defaut).
- **Routage** : `composite_notifier.py` - un seul objet `Notifier` cote moteur, qui delegue a Mailjet ou Sinch selon le canal.
- **Metier pilote** : plombier (cf. `data/price-library/seed_plombier.sql`).
- **Messages** : `messages.py` - gabarits par palier (ton chaleureux, spec 3.4), textes de depart a affiner avec un artisan pilote.

## Lancer le batch (cron)

```bash
python3 cli.py --db /chemin/vers/artisia.db
```

Necessite `MAILJET_API_KEY`/`MAILJET_API_SECRET` et `SINCH_API_KEY`/`SINCH_API_SECRET`/`SINCH_SENDER`
dans l'environnement (cf. `.env.example`) et une base avec `data/schema.sql` deja applique.
Exemple crontab (tous les jours a 9h) :

```cron
0 9 * * * cd /chemin/artisia/services/relances && /usr/bin/python3 cli.py --db /chemin/artisia/data/artisia.db >> /var/log/artisia-relances.log 2>&1
```

Tests : `python3 -m unittest test_engine.py test_mailjet_notifier.py test_sinch_notifier.py test_composite_notifier.py test_messages.py test_cli.py` (depuis ce dossier).
