# La Bonne Truffe

Outil personnel de Léo Guillaume pour trouver un chiot cocker spaniel anglais : il surveille toutes les heures les sources d'annonces de portées en France, applique les critères de Léo (race, couleur, LOF, départements, sexe), et le prévient par notification dès qu'une portée correspond, y compris les portées **à naître** déclarées à la Centrale Canine.

Ce dépôt contient le **cadrage complet** et le code de l'application :

- `api/` : FastAPI, SQLAlchemy et SQLite, worker APScheduler, collecteur Centrale Canine, Web Push.
- `web/` : Nuxt 4, Tailwind v4 et Nuxt UI, PWA avec Web Push, empaquetée en Tauri 2 pour Windows (`web/src-tauri/`).
- `docker-compose.yml` : l'API et le worker en conteneurs, la base SQLite dans un volume.
- `.github/workflows/` et `deploy/nginx/` : le déploiement sur le VPS (https://la-bonne-truffe.dibodev.fr et https://api.la-bonne-truffe.dibodev.fr) et la release de l'app Windows.

Pour lancer le projet en local : [docs/10-developpement-local.md](docs/10-developpement-local.md). Pour le déployer : [docs/11-deploiement.md](docs/11-deploiement.md).

## À lire dans l'ordre

| Fichier | Contenu |
|---|---|
| [docs/00-brief-pour-l-ia-qui-code.md](docs/00-brief-pour-l-ia-qui-code.md) | Le brief de départ : rôle, jalons, règles, définition de « fini » |
| [docs/01-cadrage.md](docs/01-cadrage.md) | Le besoin, le périmètre V1, les décisions prises, les questions ouvertes |
| [docs/02-sources.md](docs/02-sources.md) | Les sources de données, avec l'API JSON de la Centrale Canine vérifiée (URL, paramètres, champs) |
| [docs/03-modele-de-donnees.md](docs/03-modele-de-donnees.md) | Les tables, le vocabulaire des couleurs, le dédoublonnage |
| [docs/04-correspondance-et-notifications.md](docs/04-correspondance-et-notifications.md) | La règle de score, les paliers, les événements qui notifient |
| [docs/05-architecture.md](docs/05-architecture.md) | FastAPI + worker, Nuxt 4 + Tauri 2, Web Push, déploiement, standards de code |
| [docs/06-maquette-et-design.md](docs/06-maquette-et-design.md) | La maquette validée, la direction artistique, les composants, l'icône |
| [docs/07-historique-des-echanges.md](docs/07-historique-des-echanges.md) | Le résumé chronologique des discussions de cadrage |
| [docs/08-idees-et-questions-ouvertes.md](docs/08-idees-et-questions-ouvertes.md) | Ce qui est gardé pour plus tard |
| [docs/10-developpement-local.md](docs/10-developpement-local.md) | Lancer l'API, le worker, le dashboard, Tauri et Docker en local ; les commandes `cli.py` |
| [docs/11-deploiement.md](docs/11-deploiement.md) | Le VPS, les workflows GitHub Actions, les secrets, nginx, le premier déploiement |

## La maquette

Maquette interactive (iPad portrait, iPhone, desktop, icône) : https://claude.ai/artifact/4uDTwYLUxdssydGN9bhb53

Les sources HTML de chaque écran sont dans [design/mockup/](design/mockup/), l'icône dans [design/icone-app.svg](design/icone-app.svg), l'illustration de cocker dans [design/illustration-cocker.svg](design/illustration-cocker.svg), les photos et leurs crédits dans [design/photos/](design/photos/).

⚠️ Les éleveurs, numéros de portée, dates et cotations de la maquette sont **inventés**. Les vraies données viendront des sources décrites dans `docs/02-sources.md`.

## Stack imposée

Même gabarit que les autres projets de Léo (DevLeadHunter) : `api/` en **FastAPI** (Python) avec un worker de collecte, `web/` en **Nuxt 4 + TypeScript strict + Tailwind v4 + Nuxt UI** servi en PWA et empaqueté en **Tauri 2** pour Windows. Notifications iPhone par **Web Push VAPID** (gratuit, sans compte Apple), reçues par l'app web ajoutée à l'écran d'accueil. Détail dans `docs/05-architecture.md`.
