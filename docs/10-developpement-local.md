# Développement local

Comment faire tourner La Bonne Truffe sur un poste de dev : l'API FastAPI et son worker, le dashboard Nuxt et la fenêtre Tauri. Le déploiement sur le VPS est dans [11-deploiement.md](11-deploiement.md).

## Prérequis

- Python 3.11 ou plus récent.
- Node.js 22 ou plus récent.
- Rust stable et, sous Windows, les outils de build de Visual Studio (pour Tauri uniquement).

## API (`api/`)

```bash
cd api
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # Windows : .venv\Scripts\pip
cp .env.example .env
```

Dans `.env`, changer au moins `SECRET_KEY` et `ADMIN_PASSWORD`. L'adresse `contact@dibodev.fr` sert à `ADMIN_EMAIL`, `VAPID_SUBJECT` et au User-Agent des sources HTML ; elle n'est jamais écrite en dur dans le code.

```bash
.venv/bin/python cli.py init-db      # migrations + seeders (départements, cocker, utilisateur, profil de départ)
.venv/bin/python cli.py vapid-keys   # coller les deux lignes affichées dans .env
.venv/bin/python main.py             # API sur http://localhost:8000, documentation sur /docs
.venv/bin/python worker.py           # worker APScheduler : un relevé par source chaque heure (5e, 20e et 35e minutes)
```

`init-db` est idempotent : il ne recrée ni ne modifie ce qui existe déjà. La base SQLite vit dans `api/data/` (ignoré par git).

**Comptes** : `init-db` crée le compte du `.env`. L'écran « Créer un compte » ne crée un compte qu'avec `SIGNUP_ENABLED=true` ; fermé (par défaut), il garde la demande dans `signup_requests` et la pousse au compte du `.env`. Sans `RESEND_API_KEY`, le lien de « Mot de passe oublié » ne part pas : l'API l'écrit dans ses logs, il suffit de l'ouvrir dans le navigateur. Il pointe vers `WEB_BASE_URL`. En production, renseigner la clé Resend et un `EMAIL_FROM` sur un domaine vérifié dans Resend.

### Commandes à la main

| Commande | Rôle |
|---|---|
| `python cli.py init-db` | Appliquer les migrations puis les seeders |
| `python cli.py vapid-keys` | Générer la paire de clés Web Push |
| `python cli.py push-test` | Envoyer une notification de test aux appareils abonnés |
| `python cli.py scc-sync` | Lire dans le JSON Centrale Canine (`litters.filters`) les `t_ID` des départements qui ont des portées, et signaler une variété inconnue des seeders |
| `python cli.py scc-sync --save-raw DOSSIER` | Idem, en enregistrant la page JSON lue pour chaque race |
| `python cli.py collect` | Relever maintenant les trois sources (Centrale Canine, Chiens de France, Chiots de France) et afficher les portées trouvées |
| `python cli.py collect --source chiens_de_france` | Idem, pour une seule source |
| `python cli.py collect --save-raw DOSSIER` | Idem, en enregistrant chaque page reçue, JSON ou HTML (nouvelles fixtures, à anonymiser comme le disent les `README.md` de `tests/fixtures/`) |

**Premier lancement réel** : `init-db` puis `collect`. Les `t_ID` des 74 départements qui avaient des portées le 28/10/2026 sont seedés, et le relevé lit tout seul ceux qui manquent. Le relevé passe par le `curl` du système, celui de Windows 10 et plus ou de Git for Windows, parce que Cloudflare refuse le client Python (`02-sources.md`). Il marche depuis le PC de Léo : 85 portées au premier relevé du 28/10/2026.

### Qualité

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m mypy .
.venv/bin/python -m pytest
```

Les tests n'appellent jamais les sites réels : la base est en mémoire, les réponses HTTP passent par `httpx.MockTransport`, les fixtures sont dans `api/tests/fixtures/`.

## Web (`web/`)

```bash
cd web
npm install
npm run dev          # http://localhost:3000, API attendue sur http://localhost:8000
```

Pour viser une autre API, définir `NUXT_PUBLIC_API_BASE` (voir `web/.env.example`). Les workflows de production la fixent à `https://api.la-bonne-truffe.dibodev.fr`.

| Script | Rôle |
|---|---|
| `npm run lint` | Prettier, ESLint, puis `vue-tsc` (le typecheck se fait dans `.nuxt-typecheck`, sans gêner un `nuxt dev` lancé) |
| `npm run lint:fix` | Corriger ce que Prettier et ESLint savent corriger |
| `npm test` | Test de fumée : construit l'app, vérifie que l'accueil se rend, que le manifest et le service worker sont servis |
| `npm run types:api` | Régénérer `app/types/api.generated.ts` depuis l'OpenAPI de l'API lancée |

### Notifications sur iPhone et iPad

Le Web Push n'est livré par iOS qu'à l'app **ajoutée à l'écran d'accueil**, servie en HTTPS. En local, tester l'abonnement dans Chrome ou Firefox sur `localhost` ; sur l'iPhone, il faut le site déployé en HTTPS. Réglages → Notifications active l'abonnement et envoie une notification de test.

## Desktop Windows (`web/src-tauri/`)

```bash
cd web
npm run tauri:dev     # Nuxt en mode desktop sur le port 1420 + fenêtre Tauri
npm run tauri:build   # installeur NSIS dans src-tauri/target/release/bundle/
```

Le build desktop est une génération statique (`NUXT_DESKTOP_BUILD=1`). La fenêtre se cache dans la zone de notification à la fermeture, une seconde instance ramène la première, et l'app vérifie au démarrage les mises à jour publiées dans les releases GitHub. Les releases sont construites par le workflow `desktop-release.yml`, qui remplace `__TAURI_UPDATER_PUBKEY__` par la clé publique de l'updater et signe l'installeur, comme dans DevLeadHunter (clés dans `11-deploiement.md`). Pas de notification native sur Windows : les alertes arrivent sur l'iPhone et l'iPad.

En release, l'app démarre avec Windows, cachée dans la zone de notification. Pour essayer le relais de la Centrale Canine en local, mettre `COLLECT_SKIPPED_SOURCES=centrale_canine` dans `api/.env` et relancer l'API : elle ne relève plus la source elle-même, et la fenêtre de `npm run tauri:dev`, une fois connectée, la relaie 30 secondes plus tard, ou tout de suite avec « Relever maintenant » sur la page Sources.
