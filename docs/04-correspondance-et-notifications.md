# Règle de correspondance et notifications

Elle tourne à chaque relevé, sur chaque `litter_group` actif, pour chaque `search_profile` actif. Le résultat va dans `listing_matches`. Le palier décide de la notification ; le score ordonne la liste. Chaque point donne une raison lisible, affichée dans « Pourquoi ce score ».

## Premier temps : les filtres durs (palier `excluded`)

Un groupe est exclu si :
- sa race n'est pas dans le profil ;
- son département n'est pas dans la liste du profil ;
- c'est une portée à naître et le profil ne les veut pas ;
- sa couleur est **certaine** et réglée sur « ignorée » (si plusieurs couleurs certaines, exclu seulement si toutes sont ignorées) ;
- le profil exige le LOF et le statut est `non_lof` ;
- le profil veut un sexe et ce sexe est **connu absent** (compteur à 0 après la naissance, ou annonce qui dit « plus que des mâles ») ;
- le prix est connu et dépasse le plafond ;
- il ne reste aucun chiot disponible (`puppies_available` à 0 : chaque chiot réservé, vendu ou adopté sur ses annonces). La portée quitte l'accueil mais reste dans le suivi ;
- ses chiots sont nés (ou, pour une saillie déclarée, étaient attendus) il y a plus de `max_puppy_age_days` jours (deux mois par défaut ; « 2 mois », « 3 mois » ou « Jamais » dans Critères) et aucune annonce active ne dit qu'il en reste : à cet âge, ils sont presque sûrement partis. La portée quitte l'accueil mais reste dans le suivi.

Une information **inconnue ne filtre jamais** : elle fait descendre dans le palier et pose un drapeau (`color_to_confirm`, `sex_unknown`, `lof_unknown`, `price_unknown`).

Un groupe dont la couleur est ambiguë et dont toutes les couleurs possibles sont « ignorées » passe en palier `ignored` (visible seulement avec le filtre, jamais notifié), pas en `excluded`.

## Deuxième temps : le palier

| Palier | Condition |
|---|---|
| `preferred` | Au moins une couleur certaine au niveau « préférée », LOF conforme à la préférence (ou préférence « peu importe »), sexe voulu présent ou préférence « peu importe » |
| `acceptable` | Tout ce qui passe les filtres durs sans remplir les conditions de « préférée » : couleur acceptable, couleur ambiguë, LOF inconnu ou non LOF en mode « préféré », sexe inconnu |
| `ignored` | Couleur ambiguë dont toutes les valeurs possibles sont ignorées |

## Troisième temps : le score (0 à 100)

| Critère | Points | Règle |
|---|---|---|
| Couleur | 0 à 40 | 40 si une couleur certaine est préférée ; 20 si acceptable ou ambiguë (contenant au moins une préférée ou acceptable) ; 10 si inconnue ; 0 sinon |
| LOF | 0 à 20 | 20 LOF ; 10 inconnu ; 0 non LOF |
| Sexe | 0 à 15 | 15 si le sexe voulu est présent (ou préférence « peu importe » et au moins un chiot) ; 5 si inconnu (à naître) ; 0 si absent |
| Fraîcheur | 0 à 15 | 15 le jour de l'apparition ou de la naissance, décroissance linéaire jusqu'à 0 à 14 jours ; une portée à naître prend l'âge de sa déclaration de saillie |
| Proximité | 0 à 10 | 10 pour le premier département de la liste, puis 10 × (1 − rang / nombre de départements), minimum 2 |
| Bonus | 0 à 5 | +3 élevage « sélectionné » (groupe 1 SCC) ; +1 si cotation du père ≥ 4 ; +1 si cotation de la mère ≥ 4 |

Le score est plafonné à 100. Il n'influence pas le palier.

Exemple de la maquette : portée née cette nuit, gold certain (+40), LOF (+20), 2 mâles 3 femelles (+15), née cette nuit (+11 car déclarée il y a quelques jours), Ille-et-Vilaine premier de la liste (+10) = **96**.

## Les événements qui notifient

Les notifications suivent des **événements**, pas des lignes. Chaque couple (groupe, type d'événement) n'est notifié qu'une fois, grâce à `listing_matches.notified_events`, sauf `availability_change`, qui part à chaque baisse.

| Événement | Quand | Canal |
|---|---|---|
| `new_preferred` | Un groupe entre pour la première fois au palier `preferred` | Push immédiat |
| `born` | Une portée à naître passe « née » (les compteurs mâles/femelles apparaissent) et le groupe est `preferred`, **ou** est dans le suivi de Léo quel que soit son palier | Push immédiat, texte avec les sexes : « Portée née chez X : 2 mâles, 3 femelles » |
| `new_acceptable` | Un groupe entre au palier `acceptable` | Récap du soir à `digest_hour` |
| `upgraded` | Un groupe passe de `acceptable` à `preferred` (couleur confirmée, LOF précisé…) | Push immédiat |
| `availability_change` | `puppies_available` baisse sur une portée suivie | Récap du soir |
| `source_down` | Une source échoue trois relevés de suite | Push, une fois par panne |
| `signup_request` | Quelqu'un tente de s'inscrire pendant que l'inscription est fermée (`05`) | Push au compte du `.env`, une fois par adresse |
| `follow_up_reminder` | L'heure du rappel d'une portée suivie est passée (`next_reminder_at`), sauf si elle est écartée ou si la portée a disparu de ses sources (le rappel est alors noté comme passé, sans push) | Push dans les cinq minutes, une fois par rappel ; un rappel déplacé repart : « C'est l'heure d'appeler Ar Ti Marellek. » |
| `source_silent` | Une source relayée par l'app Windows (`11`) n'a aucun relevé réussi depuis trois heures de journée, entre 8 h et 23 h (heure française) : aucun PC allumé avec l'app, ou l'app déconnectée. Un PC éteint la nuit n'est pas une panne ; le silence d'une journée est signalé au plus tôt à 11 h | Push, une fois par silence ; un relevé réussi clôt le silence, le suivant est de nouveau signalé |

Une disparition (`is_active` → faux) ne notifie pas, elle grise la carte. Le récap du soir n'est envoyé que s'il contient quelque chose. Il part à `digest_hour` avec ce qui a été mis de côté avant cette heure ; si le worker était arrêté à ce moment-là, l'heure pleine suivante le rattrape, une seule fois ; ce qui arrive après `digest_hour` attend le lendemain.

**Ce qui est une nouveauté** (décidé le 28/10/2026, `EventService.is_news`) : `new_preferred` et `new_acceptable` ne partent que pour une portée mise en ligne depuis **3 jours au plus**. Une portée en ligne depuis plus longtemps est notée comme traitée, sans push ni ligne dans le récap : le premier relevé, ou l'ajout d'un département aux critères, ne déverse pas les portées publiées depuis des semaines. `born` et `upgraded` partent quel que soit l'âge de la portée.

**Le premier relevé réussi d'une source** n'envoie rien du tout : il note comme traité tout ce qui était déjà en ligne avant que La Bonne Truffe la surveille, y compris les annonces sans date de publication (les portées à venir de Chiens de France). Les relevés suivants envoient les nouveautés comme ci-dessus.

**Chiot trouvé** (31/10/2026) : tant que l'utilisateur a trouvé son chiot (`puppy_arrivals`), aucune alerte de portée ne part, ni push ni ligne du récap ; les événements sont quand même notés comme traités, pour que la reprise de la recherche ne déverse pas les portées parues entre-temps. Les lignes du récap pas encore envoyées sont effacées au « C'est lui ! ». Les rappels du suivi, posés à la main, et les alertes de source continuent.

## Texte des notifications

Titre : ce qui arrive et à qui, en quelques mots (« Portée née · De Kerlann », « Passée en préférée · … », « Rappel · appeler De Kerlann », « Récap du soir · 2 portées acceptables », « La Centrale Canine ne répond plus », « Demande d'inscription ») ; iOS affiche déjà le nom de l'app. Corps : couleur, lieu, sexes, en une phrase, sans répéter le titre. Exemples :
- « Née cette nuit à Redon : une portée gold, 2 mâles et 3 femelles. Dispo vers le 22 décembre. »
- « À naître à Ploërmel : une portée gold déclarée, naissance vers le 7 novembre. »
- « 2 portées acceptables, dont 1 noir et feu à Quimper. » (titre « Récap du soir · 2 portées acceptables »)
- « De Kerlann, plus que 2 chiots disponibles. » (portée suivie, nommée comme sur sa carte)
- « Noir et feu, 2 mâles et 5 femelles (Finistère). » (titre « Rappel · appeler De Kerlann »)

L'URL de la notification ouvre le détail du groupe dans le dashboard, la page Sources pour une alerte de source. Chaque notification garde la portée qu'elle concerne et, pour le récap, ses portées avec leur événement (`notifications.digest_litters`) : la cloche les affiche avec leur vignette, leur lieu et leurs sexes (`GET /notifications`, champs `litter` et `litters`).

## Le profil de départ de Léo

```json
{
  "name": "Cocker gold Bretagne",
  "breed_ids": ["cocker-spaniel-anglais"],
  "department_codes": ["35", "56", "22", "29", "44", "53", "49", "72", "85"],
  "include_expected_litters": true,
  "sex_preference": "any",
  "lof_preference": "required",
  "color_preferences": { "gold": "preferred", "noir_et_feu": "acceptable" },
  "price_max_cents": null,
  "notify_preferred_immediately": true,
  "notify_acceptable_in_digest": true,
  "digest_hour": 19,
  "notify_birth_of_followed": true
}
```

Les couleurs absentes de `color_preferences` prennent la valeur `ignored` : Léo l'a confirmé le 28/10/2026, comme le sexe indifférent et l'absence de plafond de prix. Ce profil est créé par `api/seeders/search_profile_seeder.py`, et chaque inscription reçoit le même.

**LOF obligatoire par défaut** (décidé le 29/10/2026) : seules les portées LOF s'affichent tant que le critère « Pedigree LOF » ne change pas. « Préféré » montre aussi les portées sans papiers, en `acceptable` (récap du soir, jamais de push immédiat) ; « Peu importe » les traite comme les autres. Les profils restés sur « Préféré » sont passés à « Obligatoire » par la migration `require_lof_on_profiles_left_on_preferred` : jusque-là, aucune portée non LOF n'arrivait dans l'app, les deux réglages montraient donc les mêmes portées.

## Mise en œuvre (jalon 2)

Code : `api/services/matching/` (`tiers.py`, `scoring.py`, `matching_service.py` pur et testé, `events.py`, `match_refresh.py`), `api/services/litter_grouping.py`, `api/services/notifier.py`. Précisions prises en codant, à valider :

- **Fraîcheur** : l'âge compte depuis la mise en ligne de la portée, en heure française : la plus ancienne date de publication de ses annonces (`published_at`), ou sa première apparition dans l'app si celle-ci est plus ancienne. Une portée à naître apparaît avec sa déclaration de saillie ; sa naissance garde cet âge.
- **Raisons** : une raison par critère (« Gold, ta couleur préférée », « Portée LOF », « 2 mâles et 3 femelles », « Apparue il y a 4 jours », « Ille-et-Vilaine, ton département le plus proche », bonus). L'exemple de la maquette donne bien **96** (test `test_gold_litter_born_in_the_closest_department_scores_96_and_is_preferred`).
- **Département inconnu** : il ne filtre pas (une information inconnue ne filtre jamais) ; drapeau `department_unknown`.
- **Naissance** : quand une portée naît et passe « préférée » dans le même relevé, seul `born` part (il porte la nouvelle) ; `new_preferred` est noté comme traité.
- **Réglages coupés** : un événement que le profil ne veut pas recevoir est quand même noté comme traité, pour qu'un réglage rallumé ne déverse pas d'anciennes portées.
- **Critères modifiés** : l'enregistrement relance l'évaluation **sans notifier** (Léo regarde l'app à ce moment-là).
- **Regroupement** : deux annonces d'une même source ne sont jamais regroupées sur une supposition (une source liste une portée une fois), seulement par numéro de portée ; la règle « une seule portée candidate en 60 jours » ne vaut que pour une annonce sans date de naissance.
- **Chiots encore disponibles** (`availability_change`, ajouté le 29/10/2026) : chaque regroupement recalcule `litter_groups.puppies_available` depuis les annonces actives : le plus petit nombre donné par une annonce de portée (Chiots de France), sinon un chiot par annonce de chiot encore à vendre (Chiens de France ; une annonce réservée, vendue ou retirée ne compte plus). La Centrale Canine ne donne pas ce nombre. Quand il baisse sur une portée du suivi, une ligne part dans le récap du soir, à chaque baisse, jusqu'à « plus aucun chiot disponible » ; le récap donne le nombre au moment de l'envoi. Couper le récap du soir coupe aussi ces lignes. Une portée à zéro chiot est exclue (voir les filtres durs) ; les mâles et femelles d'une portée connue par des annonces de chiots ne comptent que les chiots encore à vendre, et la carte porte `puppies_available` (« 2 chiots dispo »).
- **Annonces de chiots** (30/10/2026) : une portée connue seulement par des annonces de chiots (Whoof, Chiens de France, Cœur de Cocker) est née : son push le dit (« Nouvelle portée, née le… »), avec ses sexes et sa date de disponibilité, comme une déclaration de naissance ; seule une saillie déclarée est « à naître ».
- Le texte des notifications met le département entre parenthèses quand la ville n'est pas connue : « Née le 27 octobre (Ille-et-Vilaine) : une portée gold, 2 mâles et 3 femelles. Dispo vers le 22 décembre. »
