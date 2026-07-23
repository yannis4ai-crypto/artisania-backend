# CLAUDE.md

> Mémoire de travail du projet. À lire avant toute session de développement.
> Dernière mise à jour : 22 juillet 2026.

---

## 1. Le projet en une phrase

Assistant administratif cloud pour artisans et TPE (métier pilote : plombier), dont la promesse est le **temps et la charge mentale récupérés** — pas la souveraineté, pas la conformité. Offre distincte de Keepia, dont elle ne partage ni la marque, ni le discours, ni l'infrastructure.

**Promesse produit** : « Tu as retrouvé tes soirées. Tu n'as plus besoin de tout garder en tête. »

---

## 2. Nom du produit — NON TRANCHÉ

Trois candidats analysés, aucun validé par un Conseil en Propriété Industrielle :

| Candidat | Classes 9/42 | Obstacle identifié |
|---|---|---|
| Artisia | Dégagées | Marque UE active en classe 35 |
| Artisania | Dégagées | Marque FR active en classe 41 (formation) |
| Appui | Dégagées | Marque FR active classes 35/36/45 (expire 09/2026) + plusieurs acteurs du bâtiment |

**Instruction de développement** : ne jamais coder le nom du produit en dur. Utiliser une constante de configuration unique (`PRODUCT_NAME`), pour qu'un changement de marque reste une modification d'une ligne. Aucun usage externe du nom avant avis du CPI.

---

## 3. Principes non négociables

Ces règles priment sur toute considération technique. En cas de doute, les respecter plutôt que d'optimiser.

1. **L'IA propose, l'artisan dispose.** Aucune action engageante (rendez-vous, devis, facture, message client) n'est envoyée sans validation humaine explicite. Pas d'envoi automatique, jamais.
2. **Transparence IA.** L'agent vocal se présente toujours comme assistant virtuel. Il ne se fait jamais passer pour l'artisan.
3. **La validation alimente le corpus.** Rien n'entre dans le RAG sans validation de l'artisan, et c'est la version *corrigée* qui est indexée — jamais la version générée brute.
4. **Annonce explicite des capacités dégradées.** Le système connaît son niveau de complétude par capacité et le dit au moment de l'usage, plutôt que de sous-performer silencieusement.
5. **Isolation stricte par artisan.** Le corpus, les prix et les données d'un artisan n'alimentent jamais ceux d'un autre. Filtrage par tenant obligatoire sur toute requête, en particulier vectorielle. Une requête RAG sans filtre tenant est un bug critique, pas une optimisation à faire plus tard.

---

## 4. Stack technique

### Décidée

| Composant | Choix |
|---|---|
| Backend | FastAPI (Python) |
| Hébergement | Render (Frankfurt) |
| Base de données | PostgreSQL managé + extension `pgvector` |
| Frontend | Jinja2 + HTMX (pas de SPA, pas de build JS) |
| Stockage objet | Cloudflare R2 (photos, vidéos, audio) |
| Email | Mailjet |
| SMS | Sinch |
| Auth | Email + lien magique (pas d'OAuth, pas de mot de passe) |
| LLM | Claude Sonnet par défaut |
| Orchestration cron | Python direct (`cli.py` + cron), **pas de n8n** |
| Mobile | Web responsive, **pas d'app native** |
| Routing (tournées) | Google Maps Routes API |

### Non tranchée — ne pas construire dessus sans décision

- **Agent vocal** : test en cours entre Retell/Vapi (construire) et Vokai (s'appuyer sur l'existant). Seuils : ≥ 80 % de qualification correcte = retenu, 60-79 % = itérer, < 60 % = abandonner.
- **STT transcription terrain** : non sourcé, distinct du choix agent vocal.
- **Téléphonie** : non sourcée. Doit supporter le renvoi conditionnel (occupé/non-réponse).
- **OCR / ingestion documentaire** : non conçu, qualité non testée sur photos de chantier.
- **Design system multi-device** : non conçu.
- **Plateforme de paiement** : non traitée.

---

## 5. Architecture

### Modèle agentique

**Backend déterministe avec appels LLM ponctuels et délimités.** Pas de framework multi-agents (LangGraph, CrewAI, AutoGen écartés) : ils ajoutent de l'imprévisibilité là où le principe de validation humaine exige de la traçabilité.

| Étape | Traitement |
|---|---|
| Conversation d'accueil | Agent hébergé par le tiers retenu — seule brique agentique réelle |
| Détection d'escalade | Logique déterministe (mot-clé, signal), pas de LLM |
| Résumé, brief, brouillon de message | Un appel LLM ponctuel : prompt → texte. Pas d'agent avec mémoire ni outils |
| Devis | Appel LLM ancré sur le RAG, validation humaine obligatoire |

### RAG

**Rôle** : fiabiliser de façon incrémentale le contenu proposé. Ce n'est pas un moteur de recherche — c'est une boucle d'ancrage. Avant de générer, on récupère les contenus passés pertinents *de cet artisan*.

- Stockage : `pgvector` dans le Postgres existant. Pas de service vectoriel séparé.
- Injection : sur validation uniquement (voir principe 3).
- Amorçage : 3 devis + 1 rapport type demandés à l'onboarding, non bloquants.
- Filtrage tenant : obligatoire (voir principe 5).

### Hors connexion

**Synchronisation au premier plan**, pas Background Sync (non supportée sur iOS Safari, tous navigateurs confondus car WebKit imposé).

- Capture locale immédiate (IndexedDB) + métadonnées.
- Tentative d'envoi à l'ouverture de l'app, plus un bouton « envoyer maintenant ».
- Indicateur visuel des éléments en attente — jamais silencieux.
- Contrainte iOS : quota de stockage ~50 Mo. Limite de durée/compression vidéo obligatoire dès la capture.

### Notifications

**SMS = canal fiable par défaut** pour tout ce qui est critique. Le push web est un confort optionnel : sur iOS il exige l'installation sur l'écran d'accueil, et son statut en UE (DMA) est incertain. Ne jamais faire dépendre une alerte critique du push.

---

## 6. État du code

| Élément | État |
|---|---|
| Moteur de relances (`services/relances/engine.py`) | **Codé, 11/11 tests passants** — séquencement J+3/J+7/J+15, anti-doublon, interrupteur manuel |
| Schéma Phase 0 (`data/schema.sql`) | Écrit — artisans, clients, devis, factures, relances |
| Bibliothèque de prix (`data/price-library/`) | Schéma + seed plombier (catalogue sans prix réels) |
| Validation devis (`services/devis/validation.py`) | Codé |
| `gmail_notifier.py` | **À supprimer** — remplacé par Mailjet + Sinch |
| `mailjet_notifier.py`, `sinch_notifier.py` | **À écrire** |
| Git | Travail staged non commité au-delà du bootstrap `f570f54` |

**Priorité immédiate côté code** : committer l'existant en commits atomiques, écrire les deux notifiers, étendre le schéma.

### Extension de schéma — une seule passe

Regrouper impérativement pour éviter deux migrations : dossier chantier, engagements, micro-CRM (historisation multi-dossiers par client), logbook (tâches + agenda transversal), champ `role`, session par device, tables `pgvector`.

---

## 7. Conventions

- Python, stdlib privilégiée (`sqlite3` en local, `unittest`). Pas de dépendance ajoutée sans raison explicite.
- Tests obligatoires pour toute logique métier. API externes toujours mockées — **aucun envoi réel pendant les tests**.
- SQL portable, pas de type propriétaire.
- Commits atomiques, un sujet par commit.
- Marquer explicitement dans les commentaires et la documentation ce qui est **décidé** vs **proposé** vs **hypothèse**. Cette distinction est structurante pour le projet.

---

## 8. Ce qu'il ne faut pas faire

- Ne pas envoyer de message, devis ou confirmation sans validation explicite de l'artisan.
- Ne pas indexer dans le RAG une version générée non validée.
- Ne pas écrire une requête vectorielle sans filtre tenant.
- Ne pas introduire n8n, de framework multi-agents, ou de SPA.
- Ne pas réutiliser les arguments Keepia (souveraineté, air-gap, RGPD) — c'est une autre marque, un autre discours.
- Ne pas coder le nom du produit en dur.
- Ne pas construire sur une brique marquée « non tranchée » en section 4.
- Ne pas faire dépendre une alerte critique des notifications push.
- Ne pas committer de clé API réelle. `.env.example` uniquement.

---

## 9. Ce qui reste ouvert

**Aucune exigence fonctionnelle** — les 33 sont tranchées. Ce qui reste :

| Nature | Éléments |
|---|---|
| Sourcing externe | Téléphonie, plateforme agent vocal, STT terrain, Plateforme Agréée facturation électronique |
| Paramètres à chiffrer | Supplément par device, contenu des trois paliers d'interface, limite de durée vidéo |
| Conceptions à produire | Design system multi-device, format d'export à documenter, schéma étendu |
| Gates externes | Avis CPI sur le nom, entretiens artisans sur le prix |

**Gate économique principal, non résolu** : à petit ticket, atteindre l'objectif de revenu implique beaucoup de clients, donc un support intensif, ce qui contredit le modèle « une personne + agents ». L'analyse de sensibilité montre qu'au même prix de 99 €/mois, il faut entre 36 et 541 clients selon le scénario de coût. **La rentabilité dépend moins du prix que du coût réel par appel et du temps de support réel** — les deux variables à mesurer en priorité pendant le pilote.

---

## 10. Documents de référence

| Document | Contenu |
|---|---|
| `artisania-projet-complet.md` | Intention, valeur, scope, stack, plan macro, sensibilité prix |
| `artisania-liste-exigences.md` | Les 33 exigences fonctionnelles + 20 non fonctionnelles |
| `artisania-registre-decisions.md` | 24 décisions tracées avec leur motif |
| `artisania-plan-pas-a-pas.md` | Séquence d'exécution avec critères de sortie |
| `artisania-comparaisons-techno.md` | Toutes les études comparatives |
| `artisania-backlog.md` | Backlog opérationnel unique |
| `artisania-doc-marketing.md` | Positionnement et arc narratif des 6 fonctions |

**Règle de tenue** : ce fichier prime sur les documents de référence en cas de contradiction. Toute décision nouvelle s'inscrit d'abord au registre, puis ici si elle affecte le développement.
