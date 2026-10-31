# Architecture

Même gabarit que DevLeadHunter (le projet de référence de Léo, dépôt `devleadhunter` : `web/` Nuxt 4 + Tauri, `api/` FastAPI). Reprendre sa structure de dossiers, ses conventions et ses briques.

## Vue d'ensemble

```
la-bonne-truffe/
├── api/                 FastAPI + worker Python
│   ├── main.py          app FastAPI, démarrage du scheduler
│   ├── core/            config (.env), database, security
│   ├── models/          SQLAlchemy (voir 03-modele-de-donnees.md)
│   ├── schemas/         Pydantic v2
│   ├── services/        classes de service (collecteurs, normalisation, matching, notifier)
│   │   ├── collectors/  centrale_canine.py, chiens_de_france.py, chiots_de_france.py, whoof.py, coeur_de_cocker.py
│   │   ├── matching/    scoring.py, tiers.py, events.py
│   │   └── push_service.py   (copié de DevLeadHunter)
│   ├── api/v1/routes/   REST
│   ├── worker.py        point d'entrée du worker (APScheduler)
│   ├── cli.py           relevé à la main, affichage, réinitialisation
│   ├── migrations/      migrations manuelles (style DevLeadHunter)
│   └── tests/           pytest, fixtures JSON/HTML enregistrées des sources
├── web/                 Nuxt 4 + Tauri 2
│   ├── app/             pages, components, composables, stores, services, types, utils
│   ├── public/sw.js     service worker Web Push (copié de DevLeadHunter)
│   └── src-tauri/       Tauri 2 (desktop Windows)
├── design/              maquette, icône, illustration, photos
├── docs/                ce cadrage
├── deploy/nginx/        confs nginx du VPS
└── .github/workflows/   déploiement de l'API et du web, release de l'app Windows
```

## Côté API (Python 3.11+)

- **FastAPI**, Pydantic v2, SQLAlchemy, SQLite (un seul fichier). Migrations manuelles comme DevLeadHunter (`migrations/run_migrations.py`).
- **Worker** : processus séparé (`python worker.py`) avec **APScheduler**. Un job par source, toutes les heures, décalés de quelques minutes. Un job à chaque heure pleine envoie le récap du soir dès que `digest_hour` est passée et qu'il n'est pas encore parti (`04`). Un job toutes les cinq minutes pousse les rappels du suivi arrivés à leur heure. Quand une source est relayée par l'app Windows (`COLLECT_SKIPPED_SOURCES`), un job horaire prévient une fois par silence qu'elle n'a aucun relevé réussi depuis trois heures de journée, entre 8 h et 23 h (`04`). Un job « nettoyage » chaque nuit à 4 h 30 vide la page brute (`raw_json`) des annonces parties de leur source depuis trois mois et supprime l'historique des changements (`listing_changes`) plus vieux que ça ; les annonces passent inactives au fil des relevés, pas la nuit.
- **Collecteurs** : une classe par source avec la même interface `collect(profile) -> list[RawListing]`. `httpx` pour les appels, `selectolax` (ou BeautifulSoup) pour le HTML. Centrale Canine en JSON avec User-Agent navigateur, Chiens de France et Chiots de France en HTML, Whoof (JSON de l'attribut `data-page`) et Cœur de Cocker (JSON WordPress) avec le User-Agent honnête ; toutes les requêtes passent par `PoliteHttpClient` (une par seconde) et le `curl` du système, car Cloudflare refuse le client Python sur la Centrale Canine (voir `02-sources.md`). Le worker relève la Centrale Canine à la minute 5, Chiens de France à la minute 20, Chiots de France à la minute 35, Whoof à la minute 45 et Cœur de Cocker à la minute 50 de chaque heure. Chaque relevé écrit une ligne `source_runs`. Sur le VPS, la Centrale Canine est relayée par l'app Windows d'un PC allumé (`POST /sources/centrale_canine/relay`).
- **Normalisation** : `RawListing` → `Listing` (vocabulaire canonique des couleurs, dates, LOF). `rapidfuzz` pour rapprocher les affixes.
- **Matching** : `MatchingService.evaluate(group, profile) -> Match` (palier, score, raisons, drapeaux). Pur, sans effet de bord, testé unitairement.
- **Événements** : `EventService.detect(previous_match, new_match, changes) -> list[Event]`, puis `NotifierService` qui envoie les push et écrit `notifications`.
- **Push** : copier `api/services/push_service.py` de DevLeadHunter (pywebpush + py_vapid, best-effort, purge des endpoints 404/410), les routes `notifications.py` (clé publique VAPID, subscribe, unsubscribe, test), le modèle `push_subscription`, et les variables `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY_B64`.
- **Auth** : JWT comme DevLeadHunter. Le jeton dure 30 jours (`ACCESS_TOKEN_EXPIRE_MINUTES`) et la session glisse : `GET /auth/me`, appelé à chaque navigation du dashboard et avant chaque vérification du relais par l'app Windows, renvoie un jeton neuf (`renewed_token`) dès que le courant a dépassé la moitié de sa vie, et l'app le garde ; un appareil qui ouvre l'app au moins une fois tous les quinze jours ne se déconnecte jamais. Le seeder crée le compte du `.env`. L'inscription est **fermée par défaut** (`SIGNUP_ENABLED=false`) : l'écran « Créer un compte » reste affiché, mais une tentative garde le prénom et l'adresse dans `signup_requests` (jamais le mot de passe), affiche « C'est noté ! » et pousse la demande au compte du `.env`, une fois par adresse ; la réponse est la même si l'adresse a déjà un compte. `SIGNUP_ENABLED=true` ouvre la création de comptes, chacun avec le profil de départ, ses suivis et ses notifications. Mot de passe oublié : un lien signé, valable 30 minutes (`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`) et à usage unique (le jeton porte une empreinte du hash du mot de passe), envoyé par Resend (`RESEND_API_KEY`, `EMAIL_FROM`) ou, sans clé, écrit dans les logs de l'API ; la réponse est la même que l'adresse ait un compte ou non, et un deuxième e-mail attend 45 secondes. L'API est exposée sur internet (le worker et l'iPhone doivent la joindre) : HTTPS obligatoire derrière le reverse proxy du VPS.
- **Qualité** : `ruff check` et `ruff format`, **mypy en mode strict** (`python -m mypy .`, plugin pydantic), `pytest`. Les colonnes à valeurs fermées sont des `StrEnum` typées côté SQLAlchemy (`models/enum_column.py`). Les tests des collecteurs tournent sur des réponses **enregistrées** (fixtures), jamais sur les sites réels.

### Endpoints REST (v1)

| Méthode et route | Rôle |
|---|---|
| `POST /auth/login`, `GET /auth/me` | Connexion ; `/me` rend l'utilisateur et, passé la moitié de la vie du jeton, un jeton neuf à garder (`renewed_token`) |
| `POST /auth/signup` | Créer un compte avec le profil de départ, et l'ouvrir ; `403` tant que l'inscription est fermée |
| `GET /auth/signup-availability`, `POST /auth/signup-requests` | Inscription ouverte ou non ; demande d'inscription gardée tant qu'elle est fermée (`202`, même réponse que l'adresse ait un compte ou non) |
| `POST /auth/forgot-password`, `POST /auth/reset-password/verify`, `POST /auth/reset-password` | Mot de passe oublié : envoi du lien, vérification du lien, nouveau mot de passe (qui connecte) |
| `GET /litters` | Groupes de portées avec leur match, filtres `tier`, `kind`, `active`, tri par score ou fraîcheur |
| `POST /litters/visit` | Noter que la liste est consultée maintenant (une fois par ouverture de l'app) ; renvoie la consultation précédente (`previous_visit_at`, `null` la première fois) |
| `GET /litters/{id}` | Détail : listings par source (pour une annonce de chiot : son sexe, ses couleurs et ses photos), éleveur, parents (nom et cotation pris sur la première annonce active qui les donne, Centrale Canine d'abord), raisons du score, changements, suivi |
| `PATCH /litters/{id}/colors` | Confirmer une ou plusieurs couleurs à la main (`confirmed`) depuis le détail, après l'appel à l'éleveur ; une liste vide retire la confirmation |
| `PATCH /litters/{id}/sexes` | Confirmer les mâles et les femelles à la main depuis le détail, quand les sources ne les donnent pas ; les deux vides retirent la confirmation (`has_confirmed_sexes` sur la carte) |
| `POST /litters/{id}/shares` | Créer le lien privé d'une portée, valable 30 jours (`{ url, expires_at }`) ; un mot facultatif l'accompagne |
| `GET /shares/{token}` | Sans compte : la page du lien (prénom de qui partage, son mot, la portée sans score, raisons ni suivi) ; `404` lien inconnu, `410` lien expiré |
| `GET /profiles`, `PUT /profiles/{id}` | Critères |
| `GET /follow-ups`, `PUT /litters/{id}/follow-up`, `POST /litters/{id}/notes` | Suivi et notes |
| `DELETE /litters/{id}/follow-up`, `DELETE /litters/{id}/notes/{note_id}` | Ne plus suivre une portée (statut, rappel et notes effacés, renvoie le détail) ; supprimer une note (`204`) |
| `GET /sources` | État de chaque source (dernier relevé, statut) |
| `POST /sources/{source}/run` | Lancer un relevé à la main |
| `POST /sources/centrale_canine/relay` | Relais de la Centrale Canine par l'app Windows : les pages à lire, puis le relevé |
| `POST /sources/centrale_canine/relay-request` | Demander un relevé de la Centrale Canine depuis le web ou le téléphone : un PC allumé le fait à sa vérification suivante |
| `GET /notifications`, `POST /notifications/read-all`, `GET /notifications/vapid-key`, `POST /notifications/subscribe`, `DELETE /notifications/subscribe`, `POST /notifications/test` | Cloche et Web Push |
| `GET /health` | Santé de l'API et de la base (503 si la base ne répond pas) |
| `GET /departments` | Référentiel des départements |

Toutes les routes sont préfixées par `/api/v1`.

## Côté web (Nuxt 4)

- **Nuxt 4**, Vue 3.5, **TypeScript strict**, Pinia, **Tailwind v4 + Nuxt UI 4**, icônes **Lucide** (`@iconify-json/lucide`, `<UIcon name="i-lucide-…">`), exactement comme DevLeadHunter (décision de Léo du 28/10/2026). Les couleurs, typographies, rayons et ombres de la maquette sont des tokens `@theme` dans `app/assets/css/main.css` (`bg-cream`, `text-coral-text`, `rounded-card`, `shadow-card`…) ; la palette `truffe` (corail) sert de couleur `primary` à Nuxt UI (`app/app.config.ts`). Le dashboard est en **français en dur** (pas d'i18n).
- **Carte des portées** (`/carte`) : Leaflet, importé côté client seulement ; fond vectoriel des départements (contours IGN Admin Express simplifiés, `web/app/assets/geo/departments.json`, licence ouverte), épingles rendues par Vue.
- **PWA** : manifest (nom « La Bonne Truffe », icône `design/icone-app.svg` déclinée en PNG), `public/sw.js` copié de DevLeadHunter, affichage `standalone`. Sur iPhone et iPad, les notifications exigent l'app **ajoutée à l'écran d'accueil** : garder l'encart explicatif de la page Réglages → Notifications de DevLeadHunter.
- **Web Push côté web** : copier `app/utils/webPush.ts`, `app/composables/useWebPush.ts`, `app/plugins/push-autosubscribe.client.ts` (auto-abonnement après un geste utilisateur, inactif dans le build desktop), `app/plugins/sw-notification-navigate.client.ts` (le clic sur une notification navigue dans la fenêtre ouverte), et la page Réglages → Notifications.
- **Tauri 2** : `src-tauri/` repris de DevLeadHunter (tray-icon, updater, single-instance, autostart : l'app démarre avec Windows, cachée dans la zone de notification), build `NUXT_DESKTOP_BUILD=1` en génération statique, détection via `useDesktopRuntime().isDesktopApp`. La commande `read_centrale_canine_page_with_curl` lit une page de la Centrale Canine avec le `curl.exe` de Windows, sans fenêtre, et `read_centrale_canine_page_in_browser` dans une fenêtre cachée du navigateur de l'app quand Cloudflare refuse `curl` ; le store `centraleCanineRelay` vérifie toutes les 5 minutes si le relevé de l'heure est dû et le relaie, après avoir fait vérifier la session par `GET /auth/me`, qui renouvelle le jeton ; une session refusée ramène la fenêtre à l'écran de connexion et arrête le relais. **Pas de notification native Windows** (décision de Léo du 28/10/2026) : les push arrivent sur l'iPhone et l'iPad via l'app ajoutée à l'écran d'accueil, pas de plugin de notification Tauri.
- **Position de l'appareil** : au premier lancement connecté, l'app demande sa position au téléphone (API de géolocalisation du navigateur, permission iOS comme pour les notifications ; store `location`, plugin `device-location.client.ts`), la garde en localStorage et la rafraîchit à chaque lancement passé six heures ; l'app Windows ne la demande que depuis Réglages. La distance à vol d'oiseau jusqu'à l'élevage (coordonnées de la Centrale Canine, `breeder_latitude` et `breeder_longitude` sur les cartes) s'écrit sur les cartes, le suivi et le détail (« à 32 km »), et « Carte » ouvre un tiroir Apple Plans, Google Maps ou Waze par liens universels, vers la position de l'élevage ou, à défaut, sa ville.
- **Reprise et pushs reçus** : l'app gardée en mémoire par iOS recharge ses écrans quand elle revient au premier plan après plus de cinq minutes (`plugins/app-resume.client.ts`, composable `useAppRefresh`), en comptant ce retour comme un nouveau lancement pour les badges « Nouveau » ; un push reçu fenêtre ouverte recharge aussi les écrans (message `notification-received` du service worker), et la pastille de l'icône de l'app installée porte le nombre de notifications non lues (API Badging d'iOS, `utils/appBadge.ts`).
- **Types** : générés depuis l'OpenAPI de FastAPI (`npm run types:api`, `openapi-typescript`) dans `app/types/api.generated.ts`, alias lisibles dans `app/types/api.ts`.
- **Écrans** : Accueil/Portées, Détail d'une portée, Critères, Suivi, Réglages (notifications, sources, compte), et hors session Connexion, Créer un compte, Mot de passe oublié, Nouveau mot de passe, et la Portée partagée (`/partage/[token]`, seule page dont les données sont chargées côté serveur, pour l'aperçu du lien). Voir `06-maquette-et-design.md`.

## Standards de code de Léo (résumé)

**TypeScript / Vue**
- `any` interdit ; `unknown` + narrowing. En plus de `strict`, `noUncheckedIndexedAccess`, `noImplicitReturns`, `noImplicitOverride`, `noFallthroughCasesInSwitch` et `noPropertyAccessFromIndexSignature` sont actifs (`nuxt.config.ts`). `defineEmits` garde sa signature en ligne (le compilateur de SFC ne résout pas les imports `~/`), la variable `emit` est annotée avec le type exporté de `app/types/`. Chaque `ref()` typé par sa variable : `const x: Ref<T> = ref(…)`, sans generic redondant. Chaque `computed()` typé : `ComputedRef<T>`. Callbacks et hooks typés : `onMounted((): void => { … })`. Paramètres et retours de fonction explicites.
- Ordre d'un SFC : `<template>`, `<script lang="ts" setup>`, `<style scoped>`.
- Props : interface exportée depuis `app/types/<ComponentName>.ts`, `defineProps({ … })` runtime avec `as PropType<T>` pour les unions, `default` explicite sur chaque prop optionnelle. `withDefaults(defineProps<…>())` interdit.
- Ordre dans `<script setup>` : imports (types d'abord), props + emits, composables, refs, computed, fonctions (JSDoc), watchers, hooks.
- CSS : classes utilitaires **Tailwind v4** sur les tokens de la maquette (jamais de couleur en dur dans un composant quand un token existe), composants **Nuxt UI** habillés dans `app/app.config.ts`, pas de style inline sauf valeur dynamique, `<style scoped>` toléré pour une animation. Une classe CSS écrite à la main suit BEM (`block`, `block__element`, `block--modifier`).
- JSDoc en anglais sur chaque fonction, méthode et classe. Pas de types dans les tags.
- Nommage explicite : pas d'abréviations, pas de `Data` / `Info` / `Item`, booléens avec sujet (`hasSelectedMaximumInterests`, `canSubmitForm`). Un composant réutilisable ne porte pas le domaine de sa première utilisation.
- Toute petite gestion ou formulaire = un tiroir `UDrawer` (ouvert par `v-model:open`, ou par le store qui le pilote comme `FollowUpDrawer`), jamais une page dédiée.
- Lint : prettier + eslint + vue-tsc, tout vert avant de dire « fini ».

**Python**
- Classes de service instanciées, pas de fonctions éparpillées. Pydantic pour les schémas. `ruff`. Tests `pytest` avec fixtures enregistrées.
- Commits : conventional commits en anglais, minuscules, ligne de sujet seule (`feat: add centrale canine collector`).

## Déploiement

Détail, secrets et premier déploiement dans `11-deploiement.md`.

- Sur le VPS, comme DevLeadHunter et sans Docker : l'API (uvicorn) et le worker en services systemd dans un venv, la base SQLite hors du dossier redéployé, le web Nuxt en SSR sous pm2, nginx et les certificats certbot devant (`deploy/nginx/`).
- Adresses : https://la-bonne-truffe.dibodev.fr pour le dashboard, https://api.la-bonne-truffe.dibodev.fr pour l'API.
- GitHub Actions : `deploy-api.yml` et `deploy-web.yml` contrôlent (ruff, mypy et pytest ; Prettier, ESLint et vue-tsc) puis déploient à chaque push sur `main` ; `desktop-release.yml` publie l'installeur Windows signé en release GitHub, où l'updater de l'app le trouve.
- Variables d'environnement, écrites dans le `.env` du VPS par `deploy-api.yml` : `SECRET_KEY`, `ADMIN_PASSWORD`, `VAPID_PUBLIC_KEY` et `VAPID_PRIVATE_KEY_B64` depuis les secrets GitHub ; `ADMIN_EMAIL`, `VAPID_SUBJECT` (mailto), `COLLECT_USER_AGENT_CONTACT`, `COLLECT_SKIPPED_SOURCES`, `DATABASE_URL`, `WEB_BASE_URL` et `CORS_ORIGINS` en clair dans le workflow.
