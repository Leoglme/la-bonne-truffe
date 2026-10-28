# Prompt de démarrage pour la session cloud

À coller tel quel dans une session Claude Code cloud ouverte sur `Leoglme/la-bonne-truffe`. Compléter d'abord le bloc « Réponses de Léo » en bas.

---

Tu es le développeur de **La Bonne Truffe**, mon outil perso pour trouver un chiot cocker spaniel anglais. Tu travailles dans ce dépôt, `Leoglme/la-bonne-truffe`, qui ne contient pour l'instant **que le cadrage et la maquette, aucun code**. Ta première session pose les fondations propres du projet.

## 1. Lis d'abord, dans cet ordre, en entier

1. `README.md` : ce qu'est l'app et l'ordre de lecture.
2. `docs/00-brief-pour-l-ia-qui-code.md` : ton brief, les jalons, les règles, la définition de « fini ».
3. `docs/01-cadrage.md` → `docs/05-architecture.md` : besoin, sources de données (l'API JSON de la Centrale Canine y est décrite et vérifiée), modèle de données, règle de score et de notifications, architecture et standards de code.
4. `docs/06-maquette-et-design.md` : la direction artistique validée. Les **sources HTML de la maquette** sont dans `design/mockup/` (un fichier par écran : iPad portrait, iPhone, desktop, icône). Ouvre-les, ce sont les références exactes de couleurs, typographies, rayons, espacements et composants. L'icône est `design/icone-app.svg`, l'illustration de cocker `design/illustration-cocker.svg`, les photos et leurs crédits dans `design/photos/`.
5. `docs/07-historique-des-echanges.md` et `docs/08-idees-et-questions-ouvertes.md` : le pourquoi des décisions et ce qui est gardé pour plus tard.

## 2. Le dépôt de référence : DevLeadHunter

Mon autre projet, `https://github.com/DevLeadHunter/devleadhunter` (public), a **exactement le même gabarit** que ce que je veux ici : `web/` en Nuxt 4 + TypeScript strict + Pinia, empaqueté en Tauri 2 pour le desktop et servi en PWA sur iPhone avec des notifications Web Push ; `api/` en FastAPI + SQLAlchemy avec migrations manuelles, seeders, services en classes, worker en arrière-plan. Clone-le à côté et **appuie-toi sur son architecture et sa propreté de code** :

- Lis `web/STANDARDS_CODE_ET_ARCHITECTURE.md` et `api/STANDARDS_CODE_ET_ARCHITECTURE.md` : ce sont mes règles, elles s'appliquent ici.
- Reprends la structure de dossiers de `web/app/` (pages, components, composables, stores, services en classes statiques, types dans `app/types/`, utils) et de `api/` (`core/`, `models/`, `schemas/`, `services/`, `api/v1/routes/`, `migrations/`, `seeders/`).
- Copie, en les adaptant au nom du projet, les briques de notifications : `api/services/push_service.py`, la route `notifications.py`, le modèle `push_subscription`, et côté web `app/utils/webPush.ts`, `app/composables/useWebPush.ts`, `app/plugins/push-autosubscribe.client.ts`, `app/plugins/sw-notification-navigate.client.ts`, `public/sw.js`, la page Réglages → Notifications avec son encart « ajoute l'app à l'écran d'accueil » pour iPhone.
- Reprends la configuration Tauri 2 de `web/src-tauri/` (tray-icon, updater, single-instance ; l'autostart n'est pas utile ici) et le build desktop en génération statique (`NUXT_DESKTOP_BUILD=1`), avec la détection `useDesktopRuntime().isDesktopApp`.
- Reprends ses scripts de lint et de typecheck (prettier, eslint, vue-tsc, ruff), son `.env.example`, sa façon de documenter (`docs/`).

Ce que tu ne reprends **pas** : tout ce qui est propre à la prospection (scrapers, campagnes, Storyblok, Stripe, Resend, templates de sites). Ici il n'y a qu'un utilisateur, pas de vente.

## 3. Ta mission dans cette session

**Jalon 0, le socle** :
- Initialise `web/` avec **Nuxt 4 à jour** (dernière version stable), TypeScript ultra strict, Pinia, **Tauri 2 à jour** (dernière version stable, cible Windows), le manifest PWA avec l'icône, le service worker et les briques Web Push copiées de DevLeadHunter. Un écran d'accueil vide mais déjà dans la direction artistique (fond crème `#FBF6EE`, Fredoka + Nunito auto-hébergées, barre d'onglets Portées / Suivi / Critères / Réglages, logo = icône arrondie + « La Bonne Truffe »).
- Initialise `api/` en FastAPI : `core/config.py` (`.env`), `core/database.py` (SQLite), les modèles SQLAlchemy de `docs/03-modele-de-donnees.md`, les migrations manuelles, un seeder pour `breeds`, `breed_varieties` et `departments` (les identifiants `t_ID` des départements se lisent dans le `<select>` de la page Centrale Canine, voir `docs/02-sources.md`), l'authentification à un utilisateur comme DevLeadHunter, les routes `notifications` (clé VAPID, abonnement, test), un `worker.py` avec APScheduler sans job encore, un `cli.py`.
- Un `docker-compose.yml` (api, worker, volume SQLite), un `README` de développement local dans `docs/`, `.env.example` pour les deux projets.
- Lint, typecheck et `pytest` verts. Un test de fumée côté API (l'app démarre, `/health` répond) et côté web (la page d'accueil se rend).

**Jalon 1 si tu as encore du temps** : le collecteur Centrale Canine décrit dans `docs/00-brief-pour-l-ia-qui-code.md`, avec sa commande `cli.py collect` et ses tests sur une réponse JSON enregistrée.

## 4. Règles

- Les docs sont la source de vérité. Si une source ne renvoie pas ce que les docs décrivent, c'est la source qui a raison : consigne l'écart dans `docs/02-sources.md` ou `docs/07-historique-des-echanges.md`.
- Politesse envers les sources : un relevé par heure, une requête par seconde, User-Agent honnête (navigateur pour la Centrale Canine, qui le refuse sinon). Leboncoin et Facebook ne sont jamais collectés.
- Aucune donnée inventée, aucune photo ni nom d'éleveur inventé. La maquette fait foi pour l'interface, l'iPad en portrait d'abord. Le dashboard est en français en dur.
- Standards de code : TypeScript sans `any`, props runtime typées avec `PropType` et `default` explicite, JSDoc sur chaque fonction, méthode, classe et `defineProps`, BEM, classes de service côté Python, ruff. Un nom se comprend sans ouvrir le fichier.
- Travaille sur une branche `feat/scaffold-nuxt-tauri-fastapi`, commits conventionnels en anglais et en minuscules (`feat: …`, `chore: …`), **ouvre une pull request** en fin de session avec un résumé de ce qui est fait, de ce qui reste, et des écarts avec les docs. Ne fusionne pas.
- Avant de dire « fini », vérifie dans les deux thèmes si tu as un thème sombre, à 375 px et en portrait iPad, et relis le diff contre les standards.

## 5. Réponses de Léo aux questions ouvertes

- Couleurs autres que gold et noir et feu : [acceptable / ignorée]
- Sexe : [mâle / femelle / indifférent]
- Plafond de prix : [montant ou aucun]
- Départements, du plus proche au plus loin : [35, 56, 22, 29, 44, 53, 49, 72, 85 ou ta liste]
- Styles : [Tailwind v4 comme DevLeadHunter / CSS et BEM sans Tailwind] (si Tailwind, mets `docs/05-architecture.md` et `docs/06-maquette-et-design.md` à jour)
- Adresse mail pour le User-Agent et le sujet VAPID : [adresse]
- Notification native sur Windows depuis la fenêtre Tauri : [oui, plugin de notification Tauri / non, le navigateur suffit]
