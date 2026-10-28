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

- Site : `https://www.chiens-de-france.com/`. Héberge les sites d'éleveurs de chiens de race et publie leurs annonces de chiots (LOF surtout), avec photos, prix, dates, disponibilité.
- Filtres de la page d'accueil : race et région. Pas de filtre département, sexe, couleur ou prix en page de liste ; ces informations sont dans chaque annonce.
- **Aucune alerte, aucun flux RSS.**
- Chaque annonce indique l'affixe ou « Sans Affixe », le code postal et la ville, souvent le texte libre de la couleur (« rouge / golden », « noir et feu »), le nombre de chiots et de disponibles, le prix, les parents.
- Collecte : page de liste race + région en HTML, puis page de chaque annonce nouvelle ou modifiée. Comparer un hash du contenu normalisé pour détecter les changements.
- La structure HTML exacte n'a pas été relevée : la lire au premier développement et la consigner ici.

## 3. Chiots de France

- Site : `https://www.chiots-de-france.com/`. Annonces de particuliers **et** d'éleveurs, LOF ou non.
- Filtres : race (obligatoire) et localisation (« Toute la France » par défaut). Pas de filtre sexe ; chaque annonce donne le nombre de mâles et de femelles.
- **Aucune alerte, aucun flux RSS.**
- Collecte : même logique que Chiens de France. C'est la source des annonces **non LOF**.

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
