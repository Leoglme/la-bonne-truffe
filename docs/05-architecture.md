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
│   │   ├── collectors/  centrale_canine.py, chiens_de_france.py, chiots_de_france.py
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
└── docker-compose.yml   api + worker + volume SQLite
```

## Côté API (Python 3.11+)

- **FastAPI**, Pydantic v2, SQLAlchemy, SQLite (fichier dans un volume). Migrations manuelles comme DevLeadHunter (`migrations/run_migrations.py`).
- **Worker** : processus séparé (`python worker.py`) avec **APScheduler**. Un job par source, toutes les heures, décalés de quelques minutes. Un job « récap du soir » à `digest_hour`. Un job « nettoyage » quotidien (`is_active`, purge des `raw_json` de plus de 90 jours).
- **Collecteurs** : une classe par source avec la même interface `collect(profile) -> list[RawListing]`. `httpx` pour les appels, `selectolax` (ou BeautifulSoup) pour le HTML. Centrale Canine en JSON avec User-Agent navigateur ; Cloudflare y refuse le client Python (voir `02-sources.md` et `08`). Chaque collecteur écrit une ligne `source_runs`.
- **Normalisation** : `RawListing` → `Listing` (vocabulaire canonique des couleurs, dates, LOF). `rapidfuzz` pour rapprocher les affixes.
- **Matching** : `MatchingService.evaluate(group, profile) -> Match` (palier, score, raisons, drapeaux). Pur, sans effet de bord, testé unitairement.
- **Événements** : `EventService.detect(previous_match, new_match, changes) -> list[Event]`, puis `NotifierService` qui envoie les push et écrit `notifications`.
- **Push** : copier `api/services/push_service.py` de DevLeadHunter (pywebpush + py_vapid, best-effort, purge des endpoints 404/410), les routes `notifications.py` (clé publique VAPID, subscribe, unsubscribe, test), le modèle `push_subscription`, et les variables `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY_B64`.
- **Auth** : un seul utilisateur, JWT comme DevLeadHunter. L'API est exposée sur internet (le worker et l'iPhone doivent la joindre) : HTTPS obligatoire derrière le reverse proxy du VPS.
- **Qualité** : `ruff check` et `ruff format`, **mypy en mode strict** (`python -m mypy .`, plugin pydantic), `pytest`. Les colonnes à valeurs fermées sont des `StrEnum` typées côté SQLAlchemy (`models/enum_column.py`). Les tests des collecteurs tournent sur des réponses **enregistrées** (fixtures), jamais sur les sites réels.

### Endpoints REST (v1)

| Méthode et route | Rôle |
|---|---|
| `POST /auth/login`, `GET /auth/me` | Connexion |
| `GET /litters` | Groupes de portées avec leur match, filtres `tier`, `kind`, `active`, tri par score ou fraîcheur |
| `GET /litters/{id}` | Détail : listings par source, éleveur, raisons du score, changements, suivi |
| `PATCH /litters/{id}/colors` | Confirmer une couleur à la main (`confirmed`) |
| `GET /profiles`, `PUT /profiles/{id}` | Critères |
| `GET /follow-ups`, `PUT /litters/{id}/follow-up`, `POST /litters/{id}/notes` | Suivi et notes |
| `GET /sources` | État de chaque source (dernier relevé, statut) |
| `POST /sources/{source}/run` | Lancer un relevé à la main |
| `GET /notifications`, `POST /notifications/read-all`, `GET /notifications/vapid-key`, `POST /notifications/subscribe`, `DELETE /notifications/subscribe`, `POST /notifications/test` | Cloche et Web Push |
| `GET /health` | Santé de l'API et de la base (503 si la base ne répond pas) |

Toutes les routes sont préfixées par `/api/v1`.
| `GET /departments`, `GET /breeds` | Référentiels |

## Côté web (Nuxt 4)

- **Nuxt 4**, Vue 3.5, **TypeScript strict**, Pinia, **Tailwind v4 + Nuxt UI 4**, icônes **Lucide** (`@iconify-json/lucide`, `<UIcon name="i-lucide-…">`), exactement comme DevLeadHunter (décision de Léo du 28/10/2026). Les couleurs, typographies, rayons et ombres de la maquette sont des tokens `@theme` dans `app/assets/css/main.css` (`bg-cream`, `text-coral-text`, `rounded-card`, `shadow-card`…) ; la palette `truffe` (corail) sert de couleur `primary` à Nuxt UI (`app/app.config.ts`). Le dashboard est en **français en dur** (pas d'i18n).
- **PWA** : manifest (nom « La Bonne Truffe », icône `design/icone-app.svg` déclinée en PNG), `public/sw.js` copié de DevLeadHunter, affichage `standalone`. Sur iPhone et iPad, les notifications exigent l'app **ajoutée à l'écran d'accueil** : garder l'encart explicatif de la page Réglages → Notifications de DevLeadHunter.
- **Web Push côté web** : copier `app/utils/webPush.ts`, `app/composables/useWebPush.ts`, `app/plugins/push-autosubscribe.client.ts` (auto-abonnement après un geste utilisateur, inactif dans le build desktop), `app/plugins/sw-notification-navigate.client.ts` (le clic sur une notification navigue dans la fenêtre ouverte), et la page Réglages → Notifications.
- **Tauri 2** : `src-tauri/` repris de DevLeadHunter (tray-icon, updater, single-instance ; pas d'autostart), build `NUXT_DESKTOP_BUILD=1` en génération statique, détection via `useDesktopRuntime().isDesktopApp`. **Pas de notification native Windows** (décision de Léo du 28/10/2026) : les push arrivent sur l'iPhone et l'iPad via l'app ajoutée à l'écran d'accueil, pas de plugin de notification Tauri.
- **Types** : générés depuis l'OpenAPI de FastAPI (`npm run types:api`, `openapi-typescript`) dans `app/types/api.generated.ts`, alias lisibles dans `app/types/api.ts`.
- **Écrans** : Accueil/Portées, Détail d'une portée, Critères, Suivi, Réglages (notifications, sources, compte). Voir `06-maquette-et-design.md`.

## Standards de code de Léo (résumé)

**TypeScript / Vue**
- `any` interdit ; `unknown` + narrowing. En plus de `strict`, `noUncheckedIndexedAccess`, `noImplicitReturns`, `noImplicitOverride`, `noFallthroughCasesInSwitch` et `noPropertyAccessFromIndexSignature` sont actifs (`nuxt.config.ts`). `defineEmits` garde sa signature en ligne (le compilateur de SFC ne résout pas les imports `~/`), la variable `emit` est annotée avec le type exporté de `app/types/`. Chaque `ref()` typé : `const x: Ref<T> = ref<T>(…)`. Chaque `computed()` typé : `ComputedRef<T>`. Callbacks et hooks typés : `onMounted((): void => { … })`. Paramètres et retours de fonction explicites.
- Ordre d'un SFC : `<template>`, `<script lang="ts" setup>`, `<style scoped>`.
- Props : interface exportée depuis `app/types/<ComponentName>.ts`, `defineProps({ … })` runtime avec `as PropType<T>` pour les unions, `default` explicite sur chaque prop optionnelle, JSDoc au-dessus. `withDefaults(defineProps<…>())` interdit.
- Ordre dans `<script setup>` : imports (types d'abord), props + emits, composables, refs, computed, fonctions (JSDoc), watchers, hooks.
- CSS : classes utilitaires **Tailwind v4** sur les tokens de la maquette (jamais de couleur en dur dans un composant quand un token existe), composants **Nuxt UI** habillés dans `app/app.config.ts`, pas de style inline sauf valeur dynamique, `<style scoped>` toléré pour une animation. Une classe CSS écrite à la main suit BEM (`block`, `block__element`, `block--modifier`).
- JSDoc en anglais sur chaque fonction, méthode, classe et `defineProps`. Pas de types dans les tags.
- Nommage explicite : pas d'abréviations, pas de `Data` / `Info` / `Item`, booléens avec sujet (`hasSelectedMaximumInterests`, `canSubmitForm`). Un composant réutilisable ne porte pas le domaine de sa première utilisation.
- Toute petite gestion ou formulaire = un drawer sur une pile Pinia (`useDrawerStackStore`), jamais une page dédiée.
- Lint : prettier + eslint + vue-tsc, tout vert avant de dire « fini ».

**Python**
- Classes de service instanciées, pas de fonctions éparpillées. Pydantic pour les schémas. `ruff`. Tests `pytest` avec fixtures enregistrées.
- Commits : conventional commits en anglais, minuscules, ligne de sujet seule (`feat: add centrale canine collector`).

## Déploiement

- Docker Compose sur le VPS OVH de Léo : services `api` (uvicorn) et `worker`, volume `data/` pour SQLite, reverse proxy nginx existant en HTTPS.
- Variables d'environnement : `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY_B64`, `VAPID_SUBJECT` (mailto), `COLLECT_USER_AGENT_CONTACT`, `DATABASE_URL`, `API_BASE_URL`, `WEB_BASE_URL`.
- Le web Nuxt est servi en SSR ou statique sur le même VPS (pm2 comme DevLeadHunter) ; le build Tauri se fait sur le PC de Léo.
- Pas de CI obligatoire en V1 ; un `Makefile` ou des scripts `npm` pour lint, test, build, deploy suffisent.
