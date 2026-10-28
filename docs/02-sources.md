# Sources de données

Tout ce qui suit a été vérifié le 27 et 28 octobre 2026. Les sources évoluent : reconsigner ici ce qui change.

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

**Coordonnées de l'éleveur** : dans le même JSON, bloc `litters.breeders` indexé par `n_breeder`. On y lit `u_farming_affix` et `u_farming_name` (en capitales), `u_breeder_siren` (parfois vide), `u_breeder_phone` (`06…`), `u_breeder_zip_code`, `u_breeder_town` (en capitales), `u_location` (`["48.26,-1.40"]`), `u_breeder_department` (identifiant de terme, `"41"`), `u_breeder_id` (`[n_breeder_id]`) et `u_breeder_site` (son site sur la SCC). Au relevé du 28/10, 3 éleveurs sur 35 n'avaient pas de téléphone et 9 pas de position (`""` et `[]`). Le collecteur écrit noms et villes en casse française (« Saint-Aubin-du-Cormier », « Dublin's Rose ») et le téléphone en E.164.

**Limites** : la liste ne dit pas s'il reste des chiots disponibles ; une portée peut être entièrement réservée. La couleur du paquet `159` est ambiguë. Rien ne prouve que cent pour cent des portées LOF y figurent, mais la liste est très complète.

**Comment le collecteur lit cette source** (`api/services/collectors/centrale_canine.py`) :
- un appel par race du profil et **par département du profil** (`department=<t_ID>`, `variety=all`, `is_borned=all`, `sort=0`), puis page par page jusqu'à `litters.count` ; c'est le filtre qui fixe le département de chaque portée ;
- quand un département du profil n'a pas encore de `t_ID`, le relevé lit d'abord la page « tous départements » de la race (une requête) et enregistre les identifiants de `filters.department` ; un département absent de cette liste n'a pas de portée en ce moment et n'est pas relevé (le journal le dit) ;
- une requête par seconde au plus, envoyée par le `curl` du système avec un User-Agent de navigateur et `Accept: application/json` ; un `403` arrête le relevé et s'inscrit dans `source_runs`, sans relance ;
- `n_is_borned` faux → `litter_expected`, et les compteurs mâles et femelles (0 avant la naissance) sont stockés **inconnus** (null), pas zéro ; la variété donne les couleurs (`158` certaine, `159` et `317` ambiguës) ;
- l'éleveur vient du bloc `breeders` : il est retrouvé par SIREN, puis identifiant SCC, puis téléphone, puis affixe et département ; une valeur connue n'est jamais effacée ;
- `n_created` devient `published_at` : la fraîcheur et les nouveautés partent de cette date (voir `04-correspondance-et-notifications.md`) ;
- `external_id` = `n_id`. **Hypothèse à vérifier sur un vrai relevé** : la déclaration de naissance garde-t-elle le `n_id` de la déclaration de saillie ? Si oui, la naissance apparaît comme un changement de la même annonce (`kind`, `birth_date`, compteurs dans `listing_changes`) ; sinon il faudra rapprocher les deux par `n_servicing_number` lors du regroupement en portées (jalon 4).
- Une annonce absente de deux relevés de suite (dans les départements relevés) passe inactive, de même qu'une portée née depuis plus de six mois.

**Autres pages SCC utiles plus tard** : `ÉLEVEURS DE LA RACE` (annuaire), LOF Select (base de pedigrees, cotations, généalogie), la fiche du club de race (Spaniel Club Français).

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

**Comment le collecteur lit cette source** (`api/services/collectors/chiens_de_france.py`) : une liste par race et par région des départements du profil, puis la page de chaque annonce des départements du profil ; une annonce retirée entre la liste et sa page (404) est sautée. Une requête par seconde, par le `curl` du système comme les autres sources. L'éleveur est nommé par le sous-domaine de son site (`<nom>.chiens-de-france.com`), retrouvé par son SIREN quand le SIRET est donné.

## 3. Chiots de France

**Ce que c'est.** `https://www.chiots-de-france.com/` publie des annonces d'éleveurs et de particuliers, une par portée née, avec les mâles et femelles encore **disponibles**. Aucune alerte, aucun flux RSS. Pour le cocker, il reprend surtout les portées de Chiens de France : 21 de ses 22 annonces en France le 28/10/2026, la seule propre étant un croisement non LOF.

**Accès** : `curl` passe avec le User-Agent honnête. Le `robots.txt` n'interdit que les documents (`.pdf`, `.doc`…) et les pages `/annonce/contact/`, `/annonce/envoyer-a-un-ami/` et `/annonce/signaler-un-abus/` : la liste et les annonces sont permises.

**Liste d'une race** : `GET /chiots/<race>/france`, par exemple `/chiots/cocker-spaniel-anglais/france`. Toute la France tient sur une seule page (22 cartes pour le cocker le 28/10/2026). Des filtres existent en paramètres (`departement`, `male`, `femelle`, `pro`, `part`, `lof`) ; le collecteur ne s'en sert pas.
- Chaque carte est un `a.box` de `div.list-box.result`, vers `/detail-annonce-<race>_<id>_<n>.html`.
- Le département est dans le titre du lieu : `.lieu .txt`, `title="LE MANS dans le departement 72 - Sarthe"`.
- Le badge `.vign` « LOF » de la carte marque une portée LOF. Celui de la page de l'annonce ne vaut rien : il s'affiche aussi sur une annonce non LOF.
- La loi réserve le nom d'une race aux chiens inscrits à un livre généalogique : le site range les autres sous « Type Cocker Spaniel Anglais » (`.race`), cockers sans papiers et croisements mêlés. Le seul du 28/10/2026 était un « Aussiecocker ». Le collecteur écarte ces cartes (question ouverte dans `08`).

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

## 4. Leboncoin : pas collecté

Protection anti-robot forte et conditions d'utilisation qui interdisent la collecte automatisée. Léo garde sa **recherche sauvegardée** native (notification de l'app Leboncoin). L'outil peut proposer un bouton « Ouvrir ma recherche Leboncoin » avec l'URL préconstruite, rien de plus.

## 5. Facebook : à la main

Groupes et pages d'éleveurs, connexion obligatoire. Hors périmètre technique.

## 6. chien.com

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
