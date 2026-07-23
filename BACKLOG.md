# BACKLOG.md

> Point d'entrée unique du suivi. Voir `CLAUDE.md` pour les principes et la stack.
> Priorités : 🔴 bloquant · 🟠 important · 🟡 planifié · ⚪ parké

---

## 🟠 Maintenant — rien ne bloque, à faire en premier

- [ ] Committer le travail staged en commits atomiques (seul `f570f54` bootstrap existe)
- [ ] Ajouter `.DS_Store` au `.gitignore`
- [ ] **Étendre le schéma en UNE passe** : dossier chantier, engagements, micro-CRM, logbook (tâches + agenda), champ `role`, session par device, tables `pgvector`. *Deux migrations séparées = dette immédiate.*
- [ ] Écrire `services/relances/mailjet_notifier.py` + tests (API mockée)
- [ ] Écrire `services/relances/sinch_notifier.py` + tests
- [ ] Supprimer `gmail_notifier.py`, mettre à jour `.env.example`
- [ ] Vérifier que les 11 tests du moteur de relances passent sans modification
- [ ] Créer les comptes Mailjet et Sinch, authentifier le domaine (SPF/DKIM)
- [ ] Introduire la constante `PRODUCT_NAME` — le nom n'est pas tranché, ne jamais le coder en dur

---

## 🔴 Gates externes — délai non compressible, à lancer sans attendre

- [ ] **Mandater un CPI** — trois noms candidats, aucun validé. Bloque tout usage externe et toute dépense marketing.
- [ ] **Sourcer un fournisseur téléphonie** supportant le renvoi conditionnel (occupé/non-réponse). Bloque l'accueil téléphonique.
- [ ] **Sourcer les Plateformes Agréées** (facturation électronique). Réception obligatoire sept. 2026, émission TPE sept. 2027.
- [ ] **10-20 entretiens artisans** sur le prix. À sonder explicitement : le supplément par device passe-t-il, alors que l'usage nominal suppose deux appareils ?

---

## 🔴 Test agent vocal

- [ ] Ouvrir les comptes de test Retell, Vapi, Vokai
- [ ] **Vérifier le function-calling temps réel** (lecture agenda pendant l'appel) — Retell d'abord. ⚠️ Vérifier Vokai **avant** de figer la conception, sinon Retell est présélectionné de fait.
- [ ] **Vérifier le callback en cours d'appel** (escalade urgence) — même session. Si négatif : escalade juste après l'appel, dégradation acceptable.
- [ ] Préparer la grille de notation et les scénarios (urgence, demande vague, audio dégradé, accent)
- [ ] Exécuter ~30 appels par piste — **simulés d'abord, réels ensuite**
- [ ] Trancher : ≥ 80 % retenu · 60-79 % itérer · < 60 % abandonner
- [ ] Décider : un numéro de test par piste, ou un seul avec bascule manuelle

---

## 🟠 Validation de la promesse — indépendante de la technologie

- [ ] Recruter un artisan volontaire (Wizard of Oz)
- [ ] ~1 semaine d'appels traités par un humain suivant le script EF-017
- [ ] Interroger l'artisan **et** 2-3 clients appelants
- [ ] Consigner les résultats **avant** le test technique

---

## 🟠 À chiffrer / concevoir

- [ ] Montant du supplément par device
- [ ] Contenu exact des trois paliers d'interface (fonctionnalités + densité)
- [ ] Document de format d'export — engagement publié, pas improvisé
- [ ] Prompts des 3 intentions du socle MVP : visite préliminaire, chantier à évaluer, note libre
- [ ] Limite de durée / compression vidéo (quota iOS ~50 Mo)
- [ ] **Tester l'OCR sur 5-10 photos réelles** de devis papier en conditions de chantier. Repli : limiter aux documents propres.

---

## 🟡 Construction — après levée des gates

- [ ] Accueil téléphonique : webhook, fiche prospect, escalade, confirmation client, brief catégorisé
- [ ] Dashboard artisan + brief du soir
- [ ] CRM web (édition) + mobile (consultation) — 3 clics vérifiés sur iPhone 17 Pro Max **et** Pixel 9
- [ ] Capture terrain hors connexion (IndexedDB + sync au premier plan)
- [ ] Pipeline RAG — indexation **sur validation uniquement**, filtre tenant obligatoire
- [ ] Ingestion documentaire et scan à profondeur variable
- [ ] Onboarding : amorçage du corpus (3 devis + 1 rapport, non bloquant) + annonce des capacités dégradées
- [ ] Paramétrage du mode hors connexion
- [ ] Galerie de références — **hérite du démarrage à froid du RAG**, à traiter dans le même parcours

---

## 🟡 Pilote

- [ ] Recruter 2-3 artisans réels
- [ ] Instrumenter **dès le jour 1** : coût réel par appel · appels et SMS par client/mois · **temps de support réel** · conversion appel → devis → signature · délai premier contact → signature · taux de récurrence · **taux de modification des contenus proposés** (mesure du RAG)
- [ ] Vérifier la répartition iOS/Android réelle des artisans — ne pas supposer la moyenne nationale

> Les deux métriques en gras décident de la rentabilité : au même prix de 99 €/mois, il faut entre 36 et 541 clients selon le scénario de coût.

---

## 🟡 Après le pilote

- [ ] Design system multi-device
- [ ] Trois interfaces selon capacités souscrites
- [ ] Facturation par device + add-ons (intentions étendues, profondeur de scan, rétention offline, tournée)
- [ ] Intégrer Google Maps Routes API (tournées, option payante)
- [ ] Logo distinctif — compense la faiblesse juridique d'un nom descriptif
- [ ] CI (aucun workflow `.github/` à ce jour)

---

## ⚪ Parké / écarté

| Sujet | Motif |
|---|---|
| Filtre IVR avant l'agent IA | À rouvrir si la qualification déçoit sur les demandes complexes |
| Plan-projet structuré pour les chantiers | Au-delà de la logique « aide-mémoire » retenue |
| Push web iPhone | SMS suffit ; à rouvrir si le coût SMS pèse au volume |
| Test Claude vs Mistral | Claude Sonnet retenu ; à rouvrir si le coût devient significatif |
| Partenariat avec un acteur voix | Choix binaire construire vs Vokai maintenu |
| Canal texte comme point d'entrée | Remplacé par le brief du soir |
| n8n · framework multi-agents · SPA · app native | Voir `CLAUDE.md` §8 |

---

## État

**33 exigences fonctionnelles, toutes tranchées.** Ce qui reste : du sourcing, du chiffrage, de la conception. Détail dans `artisania-liste-exigences.md` et `artisania-registre-decisions.md`.
