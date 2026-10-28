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
    &is_borned=<all | 1>
    &sort=0
    &_format=json
```

- `<page>` commence à 0, 10 portées par page. La réponse porte `litters.count` (total) pour calculer le nombre de pages.
- `department` attend l'**identifiant interne** de la taxonomie, pas le numéro du département : l'Ille-et-Vilaine est `t_41`. Les identifiants se lisent une fois dans le `<select>` « Département » de la page (`<option value="t_41">35 - Ile-et-Vilaine</option>`). Les stocker dans la table `departments`. Avec `department=35`, le filtre est ignoré silencieusement (vérifié : même total).
- `variety` pour le cocker anglais : `317` = « rouge et doré » (gold), `159` = « noir, noir et feu, marron, marron et feu » (un seul paquet, la SCC ne distingue pas), le troisième identifiant = « autres couleurs » (rouans, pluricolores), à lire dans le `<select>` « Variété ».
- `is_borned=1` renvoie les portées **à naître** (saillies déclarées). `is_borned=all` renvoie tout. La valeur pour « nées seulement » est à lire dans le `<select>` « Portées » (options : Disponibles, A naître, Toutes).
- `sort=0` = cotation globale ; les autres valeurs trient par cotation du père, de la mère, par date.

**Chiffres observés le 27/10/2026 (cocker anglais)** : 650 portées en tout, 220 en rouge et doré, 150 à naître, 19 en Ille-et-Vilaine.

**Condition d'accès** : le serveur est derrière Cloudflare. Sans User-Agent de navigateur, réponse `403` avec la page « Just a moment ». Avec un User-Agent du type `Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/130.0 Safari/537.36` et `Accept: application/json`, réponse `200` avec le JSON. Pas besoin de navigateur headless. Prévoir que Cloudflare puisse durcir un jour : garder Playwright en secours, pas en V1.

**Écart observé le 28/10/2026 depuis un conteneur cloud** (session de développement) : la page et le JSON répondent `403` avec l'en-tête `cf-mitigated: challenge`, même avec le User-Agent de navigateur, `Accept: application/json` et `Accept-Language: fr-FR`. Cloudflare juge l'IP (centre de données), pas les en-têtes. Rien n'a été contourné. Conséquences :
- les identifiants `t_ID` des départements autres que `t_41` et l'identifiant de la variété « autres couleurs » n'ont pas pu être relevés ; ils restent vides en base et se lisent avec `python cli.py scc-sync` lancé depuis une IP acceptée ;
- aucune réponse JSON réelle n'a pu être enregistrée pour les tests : la fixture `api/tests/fixtures/centrale_canine/` reprend **la forme documentée ci-dessous** avec des valeurs de test explicites, à remplacer par un vrai relevé (`python cli.py collect --save-raw`) ;
- à vérifier depuis le VPS OVH avant le déploiement : si son IP est refusée aussi, le relevé devra partir de l'IP résidentielle de Léo (voir `08-idees-et-questions-ouvertes.md`).

**Forme de la réponse** : `{"cache_tags": [...], "breed": {"breed_title": "Cocker spaniel anglais", "groups_titles": {"1": "Élevages avec Affixe et sélectionnés", "2": "Élevages avec Affixe", "3": "Élevages sans Affixe"}}, "litters": {"count": 650, "node": {"<groupe>": {"n<id>": {...portée...}}}}}`. Les portées sont groupées par qualité d'élevage (clé `1`, `2`, `3`).

**Champs utiles d'une portée** (préfixe `n_`) :

| Champ | Sens |
|---|---|
| `n_id`, `n_litter_id`, `url` (`/portee/<id>`) | Identifiants et page de la portée |
| `n_litter_number` | Numéro LOF de la portée (ex. `LOF-2026017047-2026-4`), vide pour une saillie |
| `n_servicing_number`, `n_servicing_date` | Numéro de dossier et date de saillie (timestamp) |
| `n_birth_date` | Date de naissance (timestamp), vide pour une portée à naître |
| `n_is_borned` | `true` née, `false` à naître |
| `n_male_number`, `n_female_number` | Nombre de mâles et de femelles (0 avant la naissance) |
| `n_variety`, `n_variety_id` | Variété de couleur (ex. `317`) |
| `n_father_name`, `n_father_lof`, `n_father_notation` | Père, numéro LOF, cotation (1 à 6) |
| `n_mother_name`, `n_mother_lof`, `n_mother_notation` | Mère, idem |
| `n_average_notation` | Cotation globale de la portée |
| `n_breeder`, `n_breeder_id` | Identifiants de l'éleveur |
| `n_selection` | Groupe d'élevage (1 sélectionné, 2 avec affixe, 3 sans affixe) |
| `n_litter_status` | Statut interne (valeurs 2 et 3 observées, sens à confirmer) |
| `n_created`, `n_changed` | Horodatages de création et de modification côté SCC |
| `n_image_uri` | Photo éventuelle (chemin relatif au site) |

**Coordonnées de l'éleveur** (nom ou affixe, code postal, ville, téléphone, SIREN) : rendues sur la page mais **pas dans ce JSON**. Elles viennent soit d'un second appel, soit de la page `/portee/<id>`. À repérer dans l'onglet réseau du navigateur en ouvrant la page (cinq minutes). Dans le doute, lire la page de la portée en HTML.

**Limites** : la liste ne dit pas s'il reste des chiots disponibles ; une portée peut être entièrement réservée. La couleur du paquet `159` est ambiguë. Rien ne prouve que cent pour cent des portées LOF y figurent, mais la liste est très complète.

**Comment le collecteur lit cette source** (`api/services/collectors/centrale_canine.py`, jalon 1) :
- un appel par race du profil, **par département du profil** (`department=<t_ID>`, `variety=all`, `is_borned=all`, `sort=0`) puis page par page jusqu'à `litters.count` ; le tableau des champs ne donne pas de champ département, c'est donc le filtre qui fixe le département de chaque portée. Un département sans `t_ID` connu n'est pas relevé (le journal le signale) ;
- une requête par seconde au plus, User-Agent de navigateur, `Accept: application/json` ; un `403` arrête le relevé et s'inscrit dans `source_runs`, sans relance ;
- `n_is_borned` faux → `litter_expected`, et les compteurs mâles et femelles (0 avant la naissance) sont stockés **inconnus** (null), pas zéro ; la variété donne les couleurs (`317` certaine, `159` ambiguë) ; tous les champs sont lus avec tolérance (nombre ou chaîne) tant que le type réel n'est pas vérifié ;
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
