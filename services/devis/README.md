# Devis (Phase 1)

Generation assistee de devis a partir d'une description (texte/vocale) + bibliotheque de prix
par metier, sortie PDF, validation humaine obligatoire avant envoi.
Cf. `docs/Artisia_SpecFonctionnelle_2026-07-07.md` section 3.3.

Schema de donnees : `data/schema.sql` (table `devis`). Bibliotheque de prix : `data/price-library/`.

- **Validation humaine** : `validation.py` - `mark_validated()` puis `send_devis()`, qui refuse l'envoi tant que `valide_par_artisan = 0` (`DevisNonValideError`) ou si le devis n'est pas au statut `brouillon` (`DevisStatutInvalideError`).
- **Non fait** : generation LLM de la description, rendu PDF, mentions legales/TVA.

Tests : `python3 -m unittest test_validation.py` (depuis ce dossier).
