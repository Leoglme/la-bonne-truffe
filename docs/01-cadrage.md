# Cadrage

## Le besoin

Léo veut adopter un **cocker spaniel anglais**, de préférence **gold** (rouge et doré), **noir et feu** accepté, de préférence **LOF**. Chercher un chiot aujourd'hui veut dire surveiller à la main Leboncoin, Facebook, Chiens de France, la Centrale Canine et Chiots de France, sans savoir où regarder ni quand. Aucun outil n'agrège ces sources ni ne prévient selon la race, le sexe et les départements.

Vérifié le 27/10/2026 : le seul agrégateur avec alerte est chien.com, mono-source et sans filtre par département. Leboncoin a ses recherches sauvegardées. Chiens de France et Chiots de France n'ont aucune alerte. Rien ne réunit tout.

## La découverte qui change tout

La **Centrale Canine** (Société Centrale Canine, qui tient le LOF) publie un **JSON public** de toutes les portées LOF déclarées par race, avec un filtre « à naître » qui renvoie les **saillies déclarées**. Une saillie déclarée aujourd'hui, c'est une naissance dans deux mois et des chiots cessibles huit semaines plus tard : près de **quatre mois d'avance** sur une annonce Leboncoin. On y trouve le département, la variété de couleur, le nombre de mâles et de femelles à la naissance, les parents avec leurs cotations, l'éleveur avec SIREN et téléphone. Détail dans `02-sources.md`.

## Ce que fait l'outil (V1)

1. Un **worker** relève toutes les heures la Centrale Canine (JSON), Chiens de France (HTML) et Chiots de France (HTML) pour les races du profil.
2. Il **normalise** chaque portée dans un vocabulaire commun (couleurs, statut LOF, dates, sexes), la **rattache à son éleveur** et **regroupe** les annonces d'une même portée vues sur plusieurs sources.
3. Il passe chaque portée au crible des **critères** de Léo et lui donne un **score** et un **palier** (préférée, acceptable, ignorée).
4. Il **notifie** par Web Push : tout de suite pour une portée préférée ou la naissance d'une portée suivie, dans un récap du soir pour les acceptables.
5. Un **dashboard** (iPad portrait d'abord, puis iPhone et desktop) montre les portées, le détail avec le « pourquoi ce score », les critères modifiables, et un **suivi** des échanges avec les éleveurs (statut, notes, rappels).

## Ce que l'outil ne fait pas (V1)

- Pas de collecte de **Leboncoin** (protection anti-robot, conditions d'utilisation) : Léo garde sa recherche sauvegardée native.
- Pas de collecte de **Facebook** (connexion obligatoire) : à la main.
- Pas de version publique, pas de comptes multiples, pas de monétisation.
- Pas d'appel ou de message automatique aux éleveurs : l'outil prépare, Léo appelle.

## Les décisions prises

| Sujet | Décision | Pourquoi |
|---|---|---|
| Stack | Même gabarit que DevLeadHunter : `api/` FastAPI, `web/` Nuxt 4 + Tauri 2 | Exigé par Léo, c'est son environnement sur toutes ses plateformes |
| Notifications | Web Push VAPID, reçu par l'app web ajoutée à l'écran d'accueil iPhone et iPad | Déjà en place dans DevLeadHunter, gratuit, sans compte Apple |
| Format principal | **iPad en portrait** | C'est là que Léo l'utilisera le plus |
| Nom | **La Bonne Truffe** | Clin d'œil au Bon Coin, la truffe du chien qui flaire |
| Direction artistique | Crème, corail, titres ronds (Fredoka), illustrations de cocker, photos quand il y en a | Léo a rejeté une première version éditoriale (papier, serif, trois colonnes) comme trop chargée et hors thème |
| LOF | Préféré, pas obligatoire | Une annonce non LOF reste visible en « acceptable » |
| Couleurs | Gold préférée, noir et feu acceptable, **les autres ignorées** | Tranché par Léo le 28/10/2026 |
| Sexe | **Indifférent** (`any`) | Tranché par Léo le 28/10/2026 |
| Prix | **Pas de plafond** | Tranché par Léo le 28/10/2026 |
| Départements | **35, 56, 22, 29, 44, 53, 49, 72, 85**, du plus proche au plus loin depuis Rennes | Validé par Léo le 28/10/2026 |
| Notification Windows | **Non** : pas de notification native depuis Tauri, les push arrivent sur l'iPhone et l'iPad | Comme DevLeadHunter, tranché le 28/10/2026 |
| Styles | **Tailwind v4 + Nuxt UI 4 + Lucide**, comme DevLeadHunter | Tranché par Léo le 28/10/2026 |
| Adresse de contact | `contact@dibodev.fr` pour `ADMIN_EMAIL`, `VAPID_SUBJECT` et le User-Agent des sources HTML, toujours lue depuis le `.env` | Même adresse que DevLeadHunter |
| Portées à naître | Incluses | C'est l'avantage décisif de la Centrale Canine |

## Questions encore ouvertes

- Le nom de domaine et le sous-domaine sur le VPS (le build web attend `NUXT_PUBLIC_API_BASE`).
- La Centrale Canine répond-elle depuis l'IP du VPS ? Elle refuse l'IP d'un conteneur cloud (voir `02-sources.md`).
