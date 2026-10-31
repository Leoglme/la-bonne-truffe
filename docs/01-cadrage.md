# Cadrage

## Le besoin

Léo veut adopter un **cocker spaniel anglais**, de préférence **gold** (rouge et doré), **noir et feu** accepté, de préférence **LOF**. Chercher un chiot aujourd'hui veut dire surveiller à la main Leboncoin, Facebook, Chiens de France, la Centrale Canine et Chiots de France, sans savoir où regarder ni quand. Aucun outil n'agrège ces sources ni ne prévient selon la race, le sexe et les départements.

Vérifié le 27/10/2026 : le seul agrégateur avec alerte est chien.com, mono-source et sans filtre par département. Leboncoin a ses recherches sauvegardées. Chiens de France et Chiots de France n'ont aucune alerte. Rien ne réunit tout.

## La découverte qui change tout

La **Centrale Canine** (Société Centrale Canine, qui tient le LOF) publie un **JSON public** de toutes les portées LOF déclarées par race, avec un filtre « à naître » qui renvoie les **saillies déclarées**. Une saillie déclarée aujourd'hui, c'est une naissance dans deux mois et des chiots cessibles huit semaines plus tard : près de **quatre mois d'avance** sur une annonce Leboncoin. On y trouve le département, la variété de couleur, le nombre de mâles et de femelles à la naissance, les parents avec leurs cotations, l'éleveur avec SIREN et téléphone. Détail dans `02-sources.md`.

## Ce que fait l'outil (V1)

1. Un **worker** relève toutes les heures la Centrale Canine (JSON), Chiens de France (HTML), Chiots de France (HTML), Whoof et Cœur de Cocker (JSON) pour les races du profil.
2. Il **normalise** chaque portée dans un vocabulaire commun (couleurs, statut LOF, dates, sexes), la **rattache à son éleveur** et **regroupe** les annonces d'une même portée vues sur plusieurs sources.
3. Il passe chaque portée au crible des **critères** de Léo et lui donne un **score** et un **palier** (préférée, acceptable, ignorée).
4. Il **notifie** par Web Push : tout de suite pour une portée préférée ou la naissance d'une portée suivie, dans un récap du soir pour les acceptables et pour une portée suivie qui propose moins de chiots.
5. Un **dashboard** (iPad portrait d'abord, puis iPhone et desktop) montre les portées, le détail avec le « pourquoi ce score », les critères modifiables, et un **suivi** des échanges avec les éleveurs (statut, notes, rappels).

## Ce que l'outil ne fait pas (V1)

- Pas de collecte de **Leboncoin** (protection anti-robot, conditions d'utilisation) : Léo garde sa recherche sauvegardée native.
- Pas de collecte de **Facebook** (API des groupes fermée, pages réservées aux apps validées par Meta, `02-sources.md`) : à la main.
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
| LOF | **Obligatoire par défaut**, modifiable dans Critères (« Pedigree LOF » : obligatoire, préféré, peu importe) | Tranché le 29/10/2026 : les annonces sans papiers de Chiots de France mêlent cockers et croisements ; en « préféré », elles restent visibles en « acceptable » |
| Couleurs | Gold préférée, noir et feu acceptable, **les autres ignorées** | Tranché par Léo le 28/10/2026 |
| Sexe | **Indifférent** (`any`) | Tranché par Léo le 28/10/2026 |
| Prix | **Pas de plafond** | Tranché par Léo le 28/10/2026 |
| Départements | **35, 56, 22, 29, 44, 53, 49, 72, 85**, du plus proche au plus loin depuis Rennes | Validé par Léo le 28/10/2026 |
| Notification Windows | **Non** : pas de notification native depuis Tauri, les push arrivent sur l'iPhone et l'iPad | Comme DevLeadHunter, tranché le 28/10/2026 |
| Styles | **Tailwind v4 + Nuxt UI 4 + Lucide**, comme DevLeadHunter | Tranché par Léo le 28/10/2026 |
| Adresse de contact | `contact@dibodev.fr` pour `ADMIN_EMAIL`, `VAPID_SUBJECT` et le User-Agent des sources HTML, toujours lue depuis le `.env` | Même adresse que DevLeadHunter |
| Portées à naître | Incluses | C'est l'avantage décisif de la Centrale Canine |
| Hébergement | `la-bonne-truffe.dibodev.fr` (dashboard) et `api.la-bonne-truffe.dibodev.fr` (API) sur le VPS, déployés par GitHub Actions comme DevLeadHunter | Sous-domaines créés le 28/10/2026 ; détail dans `11-deploiement.md` |
| Centrale Canine sur le VPS | Relayée par l'app Windows d'un PC allumé, avec le `curl` de Windows ou, s'il est refusé, le navigateur de l'app dans une fenêtre cachée ; le worker du VPS relève les autres sources (`COLLECT_SKIPPED_SOURCES`) | Cloudflare refuse les adresses de serveur, même avec le `curl` de Windows, et le `curl` de Linux même depuis le PC (28 et 29/10/2026, `02-sources.md`) |

## Questions encore ouvertes

- Celles qui restent sont dans `08-idees-et-questions-ouvertes.md`.

## Jalon 6 : les éleveurs et les chiots un par un (décidé le 31/10/2026)

Léo veut arriver **avant** les annonces : les bonnes portées gold se réservent sur liste d'attente, souvent avant la saillie. L'objet manquant est l'éleveur. Il veut aussi plus de données sur chaque portée (photos, sexe et couleur de chaque chiot) et lever le doute sur la couleur, son critère n° 1. Maquette validée : `06-maquette-et-design.md`, canevas « Éleveurs », proposition A.

| Sujet | Décision | Pourquoi |
|---|---|---|
| Où vivent les éleveurs | Un **onglet Éleveurs** (troisième onglet, entre Suivi et Critères, sur iPad et iPhone ; entrée de la barre latérale sur desktop) : liste classée du plus prometteur au moins prometteur, recherche avec suggestions, fiche, suivi, ajout à la main | Proposition A retenue par Léo le 31/10/2026 |
| D'où viennent les éleveurs | L'**annuaire de la Centrale Canine** pour les départements du profil (relu chaque jour) et l'**annuaire du Spaniel Club Français** (toute la France, relu chaque jour avec l'annuaire), en plus des éleveurs déjà créés par les portées | Validé par Léo ; un éleveur sans portée en cours devient visible, et donc contactable en amont |
| Les chiots un par un | Pour chaque portée de la Centrale Canine : la fiche de la portée (`api/litter`), puis la fiche de chaque parent et de chaque chiot inscrit (`api/dog`) : sexe, nom, couleur exacte, cotation, santé, locus E | Demandé par Léo : « les chiots un par un, le sexe, la couleur » |
| La couleur par les parents | Deux parents gold (ou `LocE-e/e` tous les deux) ⇒ la portée est **gold, certaine**, même à naître. Un seul parent gold ⇒ gold **possible** (ambigu). Les couleurs des chiots inscrits priment sur tout, sauf une couleur confirmée à la main | C'est la génétique du locus E ; ça lève l'ambiguïté du paquet 159 et donne la couleur des portées à naître |
| Les photos | Les sites d'éleveurs hébergés par Chiens de France (`<slug>.chiens-de-france.com`) : pages des chiots en vente (chaque chiot avec son statut et ses photos), futures portées, lices, mâles et étalons (couleur, photo, puce, cotation). La Centrale Canine n'a pas de photo | Vérifié le 31/10/2026 ; c'est la seule source de photos pour les portées que seule la SCC liste, et la seule qui annonce une portée avant la saillie déclarée |
| Suivre un éleveur | Un cœur en haut à droite de la fiche ouvre le tiroir Suivre : saillie déclarée, naissance, nouvelles photos ou annonce, même pour une couleur ignorée ; statut dans le carnet (à contacter, contacté, sur liste d'attente, acompte versé), notes, rappel. Les alertes d'éleveur partent **même hors des départements** du profil | Un éleveur suivi l'est pour ses portées, où qu'il soit ; le cœur reste à sa place de toujours (jamais dans la barre du bas) |
| Ajout à la main | Un éleveur trouvé ailleurs (Facebook, panneau, bouche-à-oreille) se crée avec un nom, une ville, un lien, un téléphone, une note ; l'app propose d'abord les élevages connus qui ressemblent au nom, et rattache les portées futures à la fiche par le téléphone, le SIREN ou l'affixe et le département | Le cas vécu : « je trouve un éleveur sur Facebook, je tape son nom, ça le trouve » |
| La recherche | Un écran poussé sur iPad et iPhone, un champ à suggestions sur desktop ; sans accents, espaces ni majuscules, sur l'affixe, le nom, la ville, le code postal, le SIREN, le téléphone ; les portées en second bloc | Validé sur maquette |
| Données personnelles | On ne garde d'un chien que ce qui décrit le chien (identité, couleur, santé, cotation, parents) et d'un éleveur que ce que l'app gardait déjà. Jamais l'e-mail ni le mobile du propriétaire que la fiche chien expose | RGPD ; l'app est perso mais le dépôt est public |
