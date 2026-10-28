# Brief pour l'IA qui code La Bonne Truffe

Tu construis **La Bonne Truffe**, un outil personnel pour Léo (un seul utilisateur) qui surveille les portées de chiots et le prévient quand une portée correspond à ses critères. Tout le cadrage est dans ce dossier `docs/`. Lis-le en entier avant d'écrire une ligne de code, dans l'ordre du README.

## Ce que tu dois produire

Un dépôt avec deux projets, sur le gabarit des projets de Léo :

- `api/` : FastAPI (Python 3.11+), SQLAlchemy, SQLite, un **worker** de collecte (APScheduler) qui relève les sources toutes les heures, calcule les correspondances et envoie les notifications Web Push.
- `web/` : Nuxt 4, TypeScript strict, Pinia, servi en PWA (manifest + service worker + Web Push) et empaqueté avec Tauri 2 pour Windows.

Pas de version publique, pas de multi-utilisateur dans l'interface, mais toutes les tables portent un `user_id` (habitude de Léo, ça ne coûte rien).

## Les jalons, dans cet ordre

1. **Collecte Centrale Canine** : le worker lit le JSON public des portées (voir `02-sources.md`), les normalise, les enregistre, détecte les changements. Une commande en ligne lance un relevé à la main et affiche ce qui a été trouvé. Tests sur des réponses JSON enregistrées.
2. **Critères + correspondance + notifications** : le profil de recherche en base, la règle de score et de paliers (`04-correspondance-et-notifications.md`), les événements, l'envoi Web Push (copie des briques de DevLeadHunter listées dans `05-architecture.md`). Une portée préférée qui apparaît déclenche un push.
3. **Dashboard Nuxt** : les quatre écrans de la maquette (Accueil/Portées, Détail, Critères, Suivi) en iPad portrait d'abord, puis iPhone et desktop. Les critères se modifient dans l'app.
4. **Chiens de France et Chiots de France** : deux collecteurs HTML en plus, et le dédoublonnage des portées entre sources.
5. **Tauri 2** pour Windows, PWA installable sur iPhone, déploiement Docker sur le VPS de Léo.

Chaque jalon doit être utilisable seul. Le jalon 1 a déjà de la valeur pour Léo s'il affiche les portées en ligne de commande.

## Règles qui ne se discutent pas

- **Lis les sources avant d'affirmer.** Si quelque chose dans ces docs ne colle pas avec ce que renvoie une source, c'est la source qui a raison : note l'écart dans `docs/07-historique-des-echanges.md` et adapte.
- **Politesse envers les sources** : un passage par heure et par source au plus, un User-Agent honnête avec l'adresse mail de Léo, une requête par seconde maximum, jamais de contournement de protection. Leboncoin et Facebook ne sont **pas** collectés (voir `02-sources.md`).
- **Aucune donnée inventée** dans l'app : une information absente s'affiche comme absente ou « à confirmer », jamais comblée.
- **Standards de code de Léo** (résumé dans `05-architecture.md`) : TypeScript ultra strict sans `any`, props runtime typées, JSDoc partout, BEM, classes de service côté Python, ruff, tests pytest. Le dashboard est en français en dur.
- **Jamais de photo ou de nom d'éleveur inventé** : les éleveurs de la maquette sont fictifs.
- **La maquette fait foi pour l'interface** : couleurs, typographies, rayons, composants, barre d'onglets, illustrations de cocker en repli des photos. Détail dans `06-maquette-et-design.md`.

## Définition de « fini » pour la V1

- Le worker tourne sur le VPS, relève les trois sources toutes les heures, et Léo reçoit sur son iPhone et son iPad un push dans l'heure qui suit l'apparition d'une portée préférée, ou la naissance d'une portée à naître qu'il suit.
- Le dashboard liste les portées par score, montre le détail avec le « pourquoi ce score », permet de modifier les critères et de suivre les échanges avec les éleveurs.
- Les portées vues sur plusieurs sources n'apparaissent qu'une fois, avec les badges des sources.
- Tout ce qui a été observé sur les sources (format, champs, pièges) est consigné dans `docs/02-sources.md` pour la suite.

## Questions à poser à Léo, pas à deviner

- Les couleurs autres que gold et noir et feu : « acceptable » ou « ignorée » par défaut ?
- Un sexe préféré ou indifférent ?
- Un plafond de prix ?
- Le nom de domaine et le sous-domaine sur le VPS, l'adresse mail à mettre dans le User-Agent.
