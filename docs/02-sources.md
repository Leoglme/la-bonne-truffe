# Sources de données

Tout ce qui suit a été vérifié du 27 au 29 octobre 2026. Les sources évoluent : reconsigner ici ce qui change.

## 1. Centrale Canine (SCC) : la source principale

**Ce que c'est.** La Société Centrale Canine tient le LOF (Livre des Origines Français). Toute portée LOF suit un circuit obligatoire : déclaration de saillie dans le mois, déclaration de naissance dans les quinze jours, puis inscription des chiots. La page « chiots de la race » publie les deux étapes.

**Page publique** : `https://www.centrale-canine.fr/le-chien-de-race/cocker-spaniel-anglais/chiots-de-la-race`

**JSON public (ce que la page appelle)** :

```
GET https://www.centrale-canine.fr/api/breed/le-chien-de-race--cocker-spaniel-anglais/chiots-de-la-race/<page>
    ?department=<all | t_ID>
    &variety=<all | ID>
    &is_borned=<all | yes | no>
    &sort=0
    &_format=json
```

- `<page>` commence à 0, 10 portées par page. La réponse porte `litters.count` (total) pour calculer le nombre de pages.
- La page HTML n'a **aucun `<select>`** : ses filtres sont construits en JavaScript à partir du bloc `litters.filters` du JSON (vérifié le 28/10/2026). C'est ce bloc qui donne les identifiants :
  - `filters.department` : `{"t_41": "35 - Ile-et-Vilaine", …}`. Le paramètre `department` attend cet **identifiant interne**, pas le numéro du département : avec `department=35`, le filtre est ignoré sans erreur (vérifié : même total). La liste ne contient que les départements qui ont **au moins une portée de la race à ce moment** : 74 pour le cocker le 28/10/2026.
  - `filters.variety` : `158` « rouge et dore » (gold), `159` « noir - noir et feu marron - marron et feu » (un seul paquet, la SCC ne distingue pas), `317` « autres couleurs » (rouans, tricolore, particolore). **Correction du 28/10/2026** : le 27/10, `317` avait été pris pour le gold. C'est « autres couleurs ».
  - `filters.is_borned` : `yes` « Disponibles », `no` « A naître », `all` « Toutes ».
- `sort=0` = cotation globale ; les autres valeurs trient par cotation du père, de la mère, par date.

**Chiffres observés le 27/10/2026 (cocker anglais)** : 650 portées en tout, 220 avec `variety=317` (« autres couleurs », pris ce jour-là pour le gold), 150 avec `is_borned=1` (valeur hors de la liste `yes`, `no`, `all` : sens non confirmé), 19 en Ille-et-Vilaine.

**Condition d'accès (vérifiée le 28/10/2026)** : le serveur est derrière Cloudflare, qui juge l'adresse, les en-têtes **et l'empreinte TLS du client**.
- Depuis la connexion de Léo, un vrai navigateur reçoit `200` sans défi. `curl` de Windows (TLS du système, Schannel) reçoit `200` avec un User-Agent de navigateur et `Accept: application/json` ; avec son User-Agent par défaut, il reçoit `403` (« Just a moment », observé le 27/10).
- Depuis la même connexion, **Python est refusé** : `httpx` et `urllib` (OpenSSL) reçoivent `403` avec `cf-mitigated: challenge`, avec exactement les en-têtes qui passent avec `curl`. Rien n'a été contourné.
- Depuis un conteneur cloud et un runner GitHub Actions (IP Azure) : `403`, `cf-mitigated: challenge`. Le runner relevait en Python (`scc-sync`, `collect`) et le client du conteneur n'a pas été noté : ces refus ne prouvent donc pas que l'adresse seule est refusée.
- **Décision du 28/10/2026** : le relevé tourne sur le PC de Léo et passe par le `curl` du système (`SystemCurlTransport`). Premier relevé réel le soir même : 85 portées dans les 9 départements du profil, 12 pages ; le deuxième relevé n'a rien trouvé de nouveau ni de modifié.
- Depuis la connexion du PC, le `curl` de Linux (Ubuntu 22.04 : curl 7.81 et OpenSSL 3.0, comme le `curl` de Debian 12) reçoit `403`, `cf-mitigated: challenge`, avec les en-têtes qui passent avec le `curl` de Windows (28/10/2026, 23 h 40). Le `curl` de Windows, qui recevait `200` à 23 h 33, a reçu `403` deux secondes après, et encore à 23 h 52 : ce refus a pu mettre la connexion en défi pour un temps. **Le VPS ne relève donc pas la Centrale Canine** (`COLLECT_SKIPPED_SOURCES`, `11-deploiement.md`).
- Depuis des serveurs, avec la requête exacte du collecteur (29/10/2026) : le VPS (OVH, `curl` de Debian 12), l'hébergement mutualisé o2switch et deux runners GitHub Actions reçoivent tous `403`, `cf-mitigated: challenge`. Le runner Windows envoyait le `curl.exe` de Windows (8.21, Schannel), le client accepté depuis la connexion du PC : depuis une adresse de serveur, même lui est refusé. Le seul client accepté reste le `curl` de Windows depuis la connexion du PC.
- **Décision du 29/10/2026** : la Centrale Canine de l'API en ligne est relayée par l'app Windows d'un PC allumé (ci-dessous, et `11-deploiement.md`).
- Depuis la connexion du PC, le 29/10/2026 à 10 h 33 : le `curl` de Windows reçoit `403`, `cf-mitigated: challenge`, mais le navigateur de l'app (WebView2, dans une fenêtre cachée) lit la page en 4 secondes : `200`, JSON complet. Cloudflare y fait sa vérification JavaScript comme dans tout navigateur ; rien ne masque l'automatisation, et une vérification qui demande une action humaine fait échouer la lecture.

**Forme de la réponse** : `{"cache_tags": [...], "breed": {"breed_title": "Cocker spaniel anglais", "groups_titles": {"1": "Élevages avec Affixe et sélectionnés", "2": "Élevages avec Affixe", "3": "Élevages sans Affixe"}}, "litters": {"count": 19, "empty_text": "", "node": {"<groupe>": {"n<id>": {...portée...}}}, "breeders": {"<n_breeder>": {...éleveur...}}, "filters": {...}, "sort": {...}}}`. Les portées sont groupées par qualité d'élevage (clé `1`, `2`, `3`).

**Types des valeurs** (Drupal) : la plupart des champs sont des **listes à un élément** (`n_birth_date: [1783252800]`, `n_male_number: [2]`, `n_breeder: [85379]`), vides quand la valeur manque. Quelques-uns sont des chaînes (`n_id`, `n_variety: "158"`, `n_breeder_id`, `n_selection: "2"`, `n_litter_number`, `url`) et `n_is_borned` est un booléen. Le collecteur déballe tout avec `SccValueParser`.

**Champs utiles d'une portée** (préfixe `n_`) :

| Champ | Sens |
|---|---|
| `n_id`, `n_litter_id`, `url` (`/portee/<id>`) | Identifiants et page de la portée |
| `n_litter_number` | Numéro LOF de la portée (ex. `LOF-2026016223-2026-11`), vide pour une saillie |
| `n_servicing_number`, `n_servicing_date` | Numéro de dossier et date de saillie (timestamp) |
| `n_birth_date` | Date de naissance (timestamp), vide pour une portée à naître |
| `n_is_borned` | `true` née, `false` à naître |
| `n_male_number`, `n_female_number` | Nombre de mâles et de femelles (0 avant la naissance) |
| `n_variety`, `n_variety_id` | Variété (`"158"`) et nœud Drupal de la variété (`[345]` ; 344 pour `159`, 346 pour `317`) |
| `n_father_name`, `n_father_lof`, `n_father_notation` | Père, numéro LOF, cotation (1 à 6) |
| `n_mother_name`, `n_mother_lof`, `n_mother_notation` | Mère, idem |
| `n_average_notation` | Cotation globale de la portée |
| `n_breeder`, `n_breeder_id` | Clé de l'éleveur dans `litters.breeders`, et son identifiant d'éleveur SCC |
| `n_selection` | Groupe d'élevage, libellé dans `breed.groups_titles` (1 avec affixe et sélectionné, 2 avec affixe, 3 sans affixe) |
| `n_litter_status` | `1` sur les 21 portées à naître du relevé du 28/10, `2` ou `3` sur les nées (sens non confirmé) |
| `n_created`, `n_changed` | Mise en ligne et modification côté SCC. Plusieurs portées partagent le même `n_created` : la SCC publie par lots |
| `n_image_uri` | Photo éventuelle (chemin relatif au site) |

**Coordonnées de l'éleveur** : dans le même JSON, bloc `litters.breeders` indexé par `n_breeder`. On y lit `u_farming_affix` et `u_farming_name` (en capitales), `u_breeder_siren` (parfois vide), `u_breeder_phone` (`06…`), `u_breeder_zip_code`, `u_breeder_town` (en capitales), `u_location` (`["48.26,-1.40"]`), `u_breeder_department` (identifiant de terme, `"41"`), `u_breeder_id` (`[n_breeder_id]`) et `u_breeder_site` (son site sur la SCC). Au relevé du 28/10, 3 éleveurs sur 35 n'avaient pas de téléphone et 9 pas de position (`""` et `[]`). Le collecteur écrit noms et villes en casse française (« Saint-Aubin-du-Cormier », « Dublin's Rose ») et le téléphone en E.164. Le booléen `is_member` dit si l'éleveur est membre du club de la race, le Spaniel Club Français pour le cocker : vérifié le 29/10/2026 sur un éleveur des Côtes-d'Armor, à `true` dans les portées et présent dans la liste des membres que publie le club (plus bas).

**Limites** : la liste ne dit pas s'il reste des chiots disponibles ; une portée peut être entièrement réservée. La couleur du paquet `159` est ambiguë. Rien ne prouve que cent pour cent des portées LOF y figurent, mais la liste est très complète.

**Cotations et santé** : la grille de cotation du cocker anglais (Spaniel Club Français, validée par la SCC le 31/01/2024) donne 2 points à un chien testé pour l'APR (atrophie progressive de la rétine) et la NF (néphropathie familiale), sain ou porteur, aux hanches cotées de A à C, et 4 points à un chien sain pour les deux maladies. Les deux sont récessives : un parent sain suffit pour qu'aucun chiot ne soit atteint. L'API en tire la santé d'une portée (`genetic_screening`, `api/services/genetic_screening.py`) : « Chiots indemnes d'APR et de NF » quand un parent a 4 points ou plus, « Parents testés APR et NF » quand les deux en ont 2 ou plus.

**Comment le collecteur lit cette source** (`api/services/collectors/centrale_canine.py`) :
- un appel par race du profil et **par département du profil** (`department=<t_ID>`, `variety=all`, `is_borned=all`, `sort=0`), puis page par page jusqu'à `litters.count` ; c'est le filtre qui fixe le département de chaque portée ;
- quand un département du profil n'a pas encore de `t_ID`, le relevé lit d'abord la page « tous départements » de la race (une requête) et enregistre les identifiants de `filters.department` ; un département absent de cette liste n'a pas de portée en ce moment et n'est pas relevé (le journal le dit) ;
- une requête par seconde au plus, envoyée par le `curl` du système avec un User-Agent de navigateur et `Accept: application/json` ; un `403` arrête le relevé et s'inscrit dans `source_runs`, sans relance ;
- sur le VPS, ces requêtes partent d'un PC : l'app Windows demande à l'API les pages à lire (`POST /sources/centrale_canine/relay`), les lit avec le `curl.exe` de Windows, une par seconde, avec les en-têtes dans l'ordre que l'API donne, celui du collecteur, puis les renvoie. Dès que Cloudflare refuse `curl`, l'app lit cette page et les suivantes du relevé dans une fenêtre cachée de son navigateur, en 30 secondes au plus par page ; elle s'arrête à la première page qu'elle ne peut pas lire. L'API rejoue le relevé sur les pages reçues et redemande celles qui manquent ; quand il n'en manque plus, elle fait le relevé habituel sur ces pages (`api/services/centrale_canine_relay.py`). Un seul PC relaie à la fois, au plus une fois toutes les 55 minutes, sauf demande depuis la page Sources (`POST /sources/centrale_canine/relay-request`), qu'un PC allumé exécute à sa vérification suivante ;
- `n_is_borned` faux → `litter_expected`, et les compteurs mâles et femelles (0 avant la naissance) sont stockés **inconnus** (null), pas zéro ; la variété donne les couleurs (`158` certaine, `159` et `317` ambiguës) ;
- l'éleveur vient du bloc `breeders` : il est retrouvé par SIREN, puis identifiant SCC, puis téléphone, puis affixe et département ; une valeur connue n'est jamais effacée ; `is_member` devient `is_breed_club_member`, mis à jour à chaque relevé (un éleveur qui quitte le club le perd) ;
- `n_created` devient `published_at` : la fraîcheur et les nouveautés partent de cette date (voir `04-correspondance-et-notifications.md`) ;
- `external_id` = `n_id`, et `n_servicing_number` devient `mating_number`, que la déclaration de naissance garde (le numéro de portée `LOF-2026016223-…` le contient). Quand la naissance garde aussi le `n_id` de la saillie, elle apparaît comme un changement de la même annonce (`kind`, `birth_date`, compteurs dans `listing_changes`) ; quand elle arrive sous un nouvel identifiant, le regroupement la rattache à la saillie par le numéro de saillie (`03`). Lequel des deux fait la Centrale Canine n'a pas encore été observé sur un vrai relevé : les deux cas donnent la même portée et le même push « née ».
- Une annonce absente de deux relevés de suite (dans les départements relevés) passe inactive, de même qu'une portée née depuis plus de six mois.

**Autres pages SCC utiles plus tard** : `ÉLEVEURS DE LA RACE` (annuaire), LOF Select (base de pedigrees, cotations, généalogie).

**Spaniel Club Français** (vérifié le 29/10/2026) : le club publie sur le site de la SCC ses éleveurs membres (`GET /spaniel-club-francais/api/breeders/0?filter=1728&department=<t_ID>&_format=json`, bloc `breeders.users`) et leurs portées (`/spaniel-club-francais/api/litters/le-chien-de-race--cocker-spaniel-anglais/<page>`), qui sont les fiches du JSON ci-dessus. Rien de plus à relever : le bloc `breeders` des portées porte déjà `is_member`.

## 2. Chiens de France

**Ce que c'est.** Le site héberge les sites d'éleveurs de chiens de race et publie leurs chiots : il annonce que « tous les chiots inscrits sur Chiens de France sont inscrits au livre des origines (LOF) ». Aucune alerte, aucun flux RSS. Vérifié le 28/10/2026.

**Accès** : Cloudflare est devant, mais Python et `curl` passent avec le User-Agent honnête `LaBonneTruffe/1.0 (+mailto:…)`. Le `robots.txt` interdit entre autres `/tous-les-chiots/`, `/liste-saillie/`, `/acheter-chiot/`, `/site_eleveur/`, `/eleveurs-liste/`, les pages `contact`, `pedigree` et `signaler`, et toute adresse contenant `FK_RACE`, `ID_CHIEN` ou `ID_ELEVEUR`. Le collecteur ne lit que les trois chemins autorisés ci-dessous.

**Liste d'une race dans une région** : `GET /chiots/<race>/france/<région>`, par exemple `/chiots/cocker-spaniel-anglais/france/bretagne`. Le slug du cocker est `cocker-spaniel-anglais` (identifiant 5 ; le cocker américain est le 167). Les slugs des régions sont ceux du formulaire de recherche (`APP_CHOICE_REGION` dans la page) : `bretagne`, `pays-de-la-loire`, `normandie`, `provence-alpes-cote-dazur`, `reunion`… Une seule page par région, sans pagination observée.
- La page range les annonces sous des titres « Département 35 - Ille et Vilaine : 2 chiots » ou « Département 56 - Morbihan : 3 portées à venir », tous dans un même bloc `div.mb-resp`. Le collecteur lit donc dans l'ordre du document : chaque lien d'annonce prend le département du dernier titre lu.
- Un chiot est une carte `a.box-1` (classe `male` ou `femelle`) vers `/chiot/<id>` ; une portée à venir, une carte `a.box-saillie-mini` vers `/saillie/<id>`.
- Les sections suivantes (« Les autres annonces… en France », « … dans les autres pays ») ne listent que des liens vers d'autres régions ou pays : elles sont ignorées.

**Page d'un chiot** (`/chiot/<id>`, une annonce par chiot) :

| Donnée | Où | Exemple |
|---|---|---|
| Sexe | bloc `div.fiche-info-rgp` « Sexe » | `Mâle`, `Femelle` |
| Naissance | même bloc « Âge », note `(Né le 28.08.2026)` | |
| LOF | bloc « Inscrite au livre des origines (LOF) » | `Oui` |
| Disponibilité | bloc « Disponibilité » | `30.10.2026` (gardée dans `raw_json`) |
| Prix | `div.fiche-prix div.prix` | `A vendre 1400 €`, ou `A vendre` sans montant |
| Lieu | `div.fiche-recap`, « Lieu » | ville, puis `35133 - France` |
| Éleveur | `div.fiche-recap`, « Eleveur » : l'affixe et le lien vers son site | `https://<nom>.chiens-de-france.com/…` |
| Parents | `div.pedifich`, type « Père » ou « Mère », puis `div.nom` | |
| SIRET | « Informations supplémentaires », « Siret » | 14 chiffres |
| Publication | « Informations complémentaires » | `Annonce créée le 03.10.2026` |
| Numéro de portée | « Portée », « Code portée » | `LOF- 2026024873-2026-13`, soit le numéro de portée de la Centrale Canine avec une espace |
| Photos | `img` dont l'adresse contient `/portees/`, sans le préfixe `TN200_` des vignettes | |

Il n'y a ni couleur ni téléphone sur la page (le contact passe par un formulaire). La couleur reste donc inconnue tant qu'une autre source ne la donne pas.

**Page d'une portée à venir** (`/saillie/<id>`) : le père et la mère (un libellé « Père » ou « Mère », puis `div.nom`), puis une liste de `li` : « Site de l'éleveur » (lien `a.fichesite` « Elevage <affixe> »), « Date de saillie » (`29/08/2026`), « Lieu » (`p.lieu-ville` « 35140 Saint-Aubin-du-Cormier », `p.lieu-dep` « 35 - Ille et Vilaine - France ») et « Pro / Siret ». Pas de date de publication.

**Relevé réel du 28/10/2026** : 12 annonces dans les deux régions du profil (7 chiots, 5 portées à venir), 14 requêtes. 7 annonces ont rejoint une portée de la Centrale Canine : par le numéro de portée, ou par la date de saillie et le nom de la mère.

**Comment le collecteur lit cette source** (`api/services/collectors/chiens_de_france.py`) : une liste par race et par région des départements du profil, puis la page de chaque annonce des départements du profil ; une annonce retirée entre la liste et sa page (404) est sautée. Une requête par seconde, par le `curl` du système comme les autres sources. L'éleveur est nommé par le sous-domaine de son site (`<nom>.chiens-de-france.com`), retrouvé par son SIREN quand le SIRET est donné ; l'accueil de ce site est gardé comme site de l'éleveur (`breeders.website`), affiché dans le détail.

## 3. Chiots de France

**Ce que c'est.** `https://www.chiots-de-france.com/` publie des annonces d'éleveurs et de particuliers, une par portée née, avec les mâles et femelles encore **disponibles**. Aucune alerte, aucun flux RSS. Pour le cocker, il reprend surtout les portées de Chiens de France : 21 de ses 22 annonces en France le 28/10/2026, la seule propre étant un croisement non LOF.

**Accès** : `curl` passe avec le User-Agent honnête. Le `robots.txt` n'interdit que les documents (`.pdf`, `.doc`…) et les pages `/annonce/contact/`, `/annonce/envoyer-a-un-ami/` et `/annonce/signaler-un-abus/` : la liste et les annonces sont permises.

**Liste d'une race** : `GET /chiots/<race>/france`, par exemple `/chiots/cocker-spaniel-anglais/france`. Toute la France tient sur une seule page (22 cartes pour le cocker le 28/10/2026). Des filtres existent en paramètres (`departement`, `male`, `femelle`, `pro`, `part`, `lof`) ; le collecteur ne s'en sert pas.
- Chaque carte est un `a.box` de `div.list-box.result`, vers `/detail-annonce-<race>_<id>_<n>.html`.
- Le département est dans le titre du lieu : `.lieu .txt`, `title="LE MANS dans le departement 72 - Sarthe"`.
- Le badge `.vign` « LOF » de la carte marque une portée LOF. Celui de la page de l'annonce ne vaut rien : il s'affiche aussi sur une annonce non LOF.
- La loi réserve le nom d'une race aux chiens inscrits à un livre généalogique : le site range les autres sous « Type Cocker Spaniel Anglais » (`.race`), cockers sans papiers et croisements mêlés. Le seul du 28/10/2026 était un « Aussiecocker ». Le collecteur garde ces cartes en non LOF, quel que soit leur badge : le critère « Pedigree LOF », sur « Obligatoire » par défaut, décide si elles s'affichent (décision du 29/10/2026, `04`).

**Page d'une annonce** :

| Donnée | Où | Exemple |
|---|---|---|
| Naissance | `ul.fiche-info-tab`, « Date de naissance » | `14 mai 2026` |
| Lieu | même liste, « Lieu » | `72000 LE MANS, Pays de la Loire` |
| Disponibles | `.nbr-male-femelle` | `1 mâle disponible`, `4 mâles et 5 femelles disponibles` ; un sexe absent de la phrase n'en a plus |
| Prix | `.fiche-prix` | `1400 €`, ou « À vendre » sans montant |
| Éleveur | titre `h2.sh1` « Elevage <affixe> » et lien `a.bouton-site-eleveur` vers `<nom>.chiens-de-france.com` | un particulier n'a pas de titre |
| SIRET | `ul.fiche-info-supp`, « SIRET » | 14 chiffres, puis `(Professionnel)` |
| Publication | même liste, « Mise en ligne de l'annonce » | `17 mai 2026` |
| Parents | `.fiche-parents`, `a.fiche-pere .nom` et `a.fiche-mere .nom` | |
| Photos | la liste `const DB_PHOTOS = [...]` du script de la galerie | |

Une annonce disparue répond par une redirection 302 vers l'accueil, pas par une 404.

**Relevé réel du 28/10/2026** : 3 requêtes, la liste puis les 2 annonces des départements du profil, d'un éleveur de la Sarthe. Toutes deux ont rejoint les chiots de Chiens de France nés le même jour de la même mère, chez l'éleveur que la Centrale Canine connaissait déjà.

**Comment le collecteur lit cette source** (`api/services/collectors/chiots_de_france.py`) : la liste France de chaque race du profil, puis la page de chaque annonce des départements du profil ; une annonce retirée entre les deux (redirection vers l'accueil) est sautée. Une requête par seconde, par le `curl` du système. Une annonce devient une portée née (`litter_born`) : ses mâles et femelles sont ceux encore disponibles, son statut LOF celui de sa carte. L'éleveur est nommé comme sur Chiens de France, par le sous-domaine de son site, et retrouvé par son SIREN.

## 4. Whoof

**Ce que c'est.** `https://whoof.fr/` publie des annonces d'éleveurs avec ce qu'ils renseignent : LOF (certificat de naissance, numéros LOF des parents), naissance, mâles et femelles, robe, prix, SIREN, ville, cotations des parents, réservation. Peu de cockers : 3 annonces en France le 29/10/2026, dont une portée LOF de Mayenne absente de Chiens de France.

**Accès** (vérifié le 29/10/2026) : `curl` passe avec le User-Agent honnête et le `robots.txt` permet toutes les pages. Les conditions d'utilisation interdisent de stocker les données personnelles d'autres utilisateurs sans leur accord : le relevé garde le nom, le SIREN et la ville des élevages comme pour les autres sources, pour un usage personnel. Accès depuis le VPS non vérifié : la pastille de la source le dira au premier relevé.

**Liste d'une race** : `GET /race/<race>/annonces?page=<n>`, par exemple `/race/cocker-spaniel-anglais/annonces`, toute la France. Whoof est une app Inertia : chaque page porte ses données en JSON dans l'attribut `data-page` de sa racine. `props.ads.data` liste les annonces de la page et `props.ads.meta.last_page` donne le nombre de pages (une seule pour le cocker le 29/10/2026).

| Donnée | Champ de l'annonce | Remarque |
|---|---|---|
| Type | `type` | `born_puppy` pour des chiots nés ; les autres types sont écartés |
| Naissance | `birthdate` | instant UTC, ramené au jour français |
| Chiots | `male_count`, `female_count` | |
| Réservation | `bookingStatus` | `available` : à réserver ; `ongoing` : adoption en cours |
| LOF | `documents.birth_certificate`, `father.lof_id`, `mother.lof_id` | LOF quand le certificat est là et que les deux parents ont un numéro, sinon à confirmer |
| Robe | `coat.colors[].value` (`blanc`, `noir`, `marron-1`…), `coat.modifications` (`roaned`, `black_fawn`…) | |
| Prix | `price` | euros |
| Parents | `father.name`, `father.notation`, `mother.name`, `mother.notation` | cotation de 1 à 6 |
| Éleveur | `breeding.slug`, `breeding.breeding_name`, `breeding.siren`, `breeding.zip_code`, `breeding.city` | |
| Lien, photo, publication | `public_url`, `main_photo`, `published_at` | |

**Page du 29/10/2026** : 3 annonces, dont 2 d'une même portée de Mayenne (2 mâles à réserver, puis 1 mâle en cours d'adoption) et une de Dordogne.

**Comment le collecteur lit cette source** (`api/services/collectors/whoof.py`) : la liste de chaque race du profil, page après page jusqu'à `last_page`, une requête par seconde par le `curl` du système. Seules restent les annonces des départements du profil, lu dans le code postal de l'élevage. Une annonce de chiots nés devient une annonce de chiot (`puppy_ad`) : ses mâles et femelles sont tous disponibles tant qu'elle est à réserver, aucun ensuite. La robe ne donne une couleur, certaine, que quand ses couleurs et ses marques en nomment une sans doute (noir rouané → bleu rouan, blanc et orange → particolore…) ; sinon la couleur reste inconnue et le texte est gardé. L'éleveur est nommé par son slug Whoof et retrouvé par son SIREN.

## 5. Cœur de Cocker

**Ce que c'est.** `https://coeurdecocker.fr/` est consacré au cocker anglais. Sa page d'adoption publie des annonces d'éleveurs, un chien par annonce : chiot d'une portée née, ou adulte à replacer. 13 annonces le 29/10/2026, dont 10 en Ille-et-Vilaine, aucune disponible ce jour-là (12 adoptées, 1 réservée) : le site bouge peu, mais un relevé ne coûte qu'une requête.

**Accès** (vérifié le 29/10/2026) : `curl` passe avec le User-Agent honnête et le `robots.txt` permet `/wp-json/`. Les conditions d'utilisation interdisent de reproduire le contenu sans accord écrit : le relevé reste à usage personnel. Accès depuis le VPS non vérifié.

**JSON public (ce que la page appelle)** : `GET /wp-json/cdc/v1/adoption/annonces`, toutes les annonces dans une liste, sans pagination.

| Donnée | Champ | Exemple |
|---|---|---|
| Type | `type` | `Chiot` ; `Senior` et les autres adultes sont écartés |
| Race | `race` | `Cocker Anglais` |
| Département | `departement` | `35` |
| Sexe | `sexe` | `Mâle`, `Femelle` |
| LOF | `lof` | `oui`, `non` |
| Robe | `couleur` | `Bleu rouan`, `Autre` |
| Statut | `statut` | `disponible`, `adopte`… |
| Prix | `prix` | `800`, `1400 Euros` |
| Naissance, publication | `date_naissance`, `date` | heure française |
| Éleveur | `eleveur_slug`, `eleveur_nom` | |
| Lien, photos | `slug` (page `/adoption/chien/<slug>/`), `photos_urls` (adresses séparées par des virgules) | |

**Comment le collecteur lit cette source** (`api/services/collectors/coeur_de_cocker.py`) : une requête par relevé, puis les chiots des races et des départements du profil. Un chiot devient une annonce de chiot (`puppy_ad`) d'un seul chiot, disponible tant que son statut est `disponible`. La robe donne une couleur certaine quand son libellé en nomme une (« Bleu rouan », « Bicolore » → particolore, « Fauve » → gold…), sinon elle reste inconnue. L'éleveur est nommé par son slug Cœur de Cocker.

## 6. Leboncoin : pas collecté

Protection anti-robot forte et conditions d'utilisation qui interdisent la collecte automatisée. Léo garde sa **recherche sauvegardée** native (notification de l'app Leboncoin). L'outil peut proposer un bouton « Ouvrir ma recherche Leboncoin » avec l'URL préconstruite, rien de plus.

## 7. Facebook et Instagram : à la main

Vérifié le 29/10/2026 :
- **Groupes** : Meta a fermé l'API des groupes en avril 2024 (version 19.0 de l'API Graph), pour tout le monde, administrateurs compris. Aucun relevé possible.
- **Pages publiques d'éleveurs** : l'accès officiel (« Page Public Content Access ») demande une vérification d'entreprise et une revue de l'app par Meta, sans garantie. Les services qui changent une page en flux RSS (RSS.app, FetchRSS, payants) la récupèrent eux-mêmes en dehors des conditions de Meta et cassent sans prévenir. Un robot connecté avec un compte personnel est interdit par les conditions de Meta.
- **Instagram** : la recherche par hashtag est fermée ; l'API officielle (« Business Discovery ») lirait les publications d'une liste de comptes professionnels d'éleveurs, avec un compte professionnel relié à une page Facebook. Pas testé (`08`).
- Reste la voie manuelle : les notifications « Tous les posts » des groupes et des pages dans l'app Facebook.

## 8. chien.com

Agrégateur avec alerte e-mail par race et pays. Pas prioritaire : ses annonces recoupent celles des autres sources. Peut devenir une quatrième source plus tard si une portée y apparaît avant ailleurs.

## Politesse et robustesse

- Un relevé par heure et par source. Une requête par seconde au plus. User-Agent honnête : `LaBonneTruffe/1.0 (+mailto:<adresse de Léo>)` **sauf** pour la Centrale Canine qui exige un User-Agent de navigateur (voir plus haut).
- Mettre en cache les pages vues (ETag ou hash), ne relire une annonce que si la liste indique un changement.
- Chaque relevé écrit une ligne dans `source_runs` (début, fin, statut, nombre vu, nouveau, modifié, erreur). Le dashboard montre « Relevé il y a 12 min » et une pastille verte ou rouge par source.
- Une erreur sur une source n'empêche pas les autres. Trois échecs de suite déclenchent une notification à Léo.

## Contexte légal utile

- Depuis la loi du 30 novembre 2021 : vente de chiens et chats interdite en animalerie depuis le 1ᵉʳ janvier 2024, vente en ligne par des particuliers en principe interdite (sanctions encore floues), annonces de cession obligatoirement avec le **numéro SIREN** de l'éleveur et le numéro d'identification de l'animal, vérifications imposées aux plateformes (décret de juillet 2022).
- Conséquence : l'offre légitime se concentre chez les éleveurs déclarés, donc sur la Centrale Canine et Chiens de France. Un SIREN présent est un bon signal ; son absence sur une annonce de particulier est un drapeau « à vérifier ».
- Cession légale d'un chiot : **huit semaines minimum**. C'est la base du calcul de la date de disponibilité.
