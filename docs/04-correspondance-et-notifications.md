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
- le prix est connu et dépasse le plafond.

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

Les notifications suivent des **événements**, pas des lignes. Chaque couple (groupe, type d'événement) n'est notifié qu'une fois, grâce à `listing_matches.notified_events`.

| Événement | Quand | Canal |
|---|---|---|
| `new_preferred` | Un groupe entre pour la première fois au palier `preferred` | Push immédiat |
| `born` | Une portée à naître passe « née » (les compteurs mâles/femelles apparaissent) et le groupe est `preferred`, **ou** est dans le suivi de Léo quel que soit son palier | Push immédiat, texte avec les sexes : « Portée née chez X : 2 mâles, 3 femelles » |
| `new_acceptable` | Un groupe entre au palier `acceptable` | Récap du soir à `digest_hour` |
| `upgraded` | Un groupe passe de `acceptable` à `preferred` (couleur confirmée, LOF précisé…) | Push immédiat |
| `availability_change` | `puppies_available` baisse sur une portée suivie | Récap du soir |
| `source_down` | Une source échoue trois relevés de suite | Push, une fois par panne |

Une disparition (`is_active` → faux) ne notifie pas, elle grise la carte. Le récap du soir n'est envoyé que s'il contient quelque chose.

## Texte des notifications

Titre : « La Bonne Truffe ». Corps : couleur, lieu, sexes, en une phrase. Exemples :
- « Née cette nuit à Redon : une portée gold, 2 mâles et 3 femelles. Dispo vers le 22 décembre. »
- « À naître à Ploërmel : une portée gold déclarée, naissance vers le 7 novembre. »
- « Récap du soir : 2 portées acceptables, dont 1 noir et feu à Quimper. »

L'URL de la notification ouvre le détail du groupe dans le dashboard.

## Le profil de départ de Léo

```json
{
  "name": "Cocker gold Bretagne",
  "breed_ids": ["cocker-spaniel-anglais"],
  "department_codes": ["35", "56", "22", "29", "44", "53", "49", "72", "85"],
  "include_expected_litters": true,
  "sex_preference": "any",
  "lof_preference": "preferred",
  "color_preferences": { "gold": "preferred", "noir_et_feu": "acceptable" },
  "price_max_cents": null,
  "notify_preferred_immediately": true,
  "notify_acceptable_in_digest": true,
  "digest_hour": 19,
  "notify_birth_of_followed": true
}
```

Les couleurs absentes de `color_preferences` prennent la valeur `ignored` : Léo l'a confirmé le 28/10/2026, comme le sexe indifférent et l'absence de plafond de prix. Ce profil est créé par `api/seeders/search_profile_seeder.py`.

## Mise en œuvre (jalon 2)

Code : `api/services/matching/` (`tiers.py`, `scoring.py`, `matching_service.py` pur et testé, `events.py`, `match_refresh.py`), `api/services/litter_grouping.py`, `api/services/notifier.py`. Précisions prises en codant, à valider :

- **Fraîcheur** : l'âge compte depuis la première apparition du groupe (`first_seen_at`, en heure française). Une portée à naître apparaît avec sa déclaration de saillie, ce qui suit la règle.
- **Raisons** : une raison par critère (« Gold, ta couleur préférée », « Portée LOF », « 2 mâles et 3 femelles », « Apparue il y a 4 jours », « Ille-et-Vilaine, ton département le plus proche », bonus). L'exemple de la maquette donne bien **96** (test `test_mockup_example_scores_96_and_is_preferred`).
- **Département inconnu** : il ne filtre pas (une information inconnue ne filtre jamais) ; drapeau `department_unknown`.
- **Naissance** : quand une portée naît et passe « préférée » dans le même relevé, seul `born` part (il porte la nouvelle) ; `new_preferred` est noté comme traité.
- **Réglages coupés** : un événement que le profil ne veut pas recevoir est quand même noté comme traité, pour qu'un réglage rallumé ne déverse pas d'anciennes portées.
- **Critères modifiés** : l'enregistrement relance l'évaluation **sans notifier** (Léo regarde l'app à ce moment-là).
- **Regroupement** : deux annonces d'une même source ne sont jamais regroupées sur une supposition (une source liste une portée une fois), seulement par numéro de portée ; la règle « une seule portée candidate en 60 jours » ne vaut que pour une annonce sans date de naissance.
- **Pas encore fait** : `availability_change` (aucune source relevée ne donne encore le nombre de chiots disponibles).
- Le texte des notifications met le département entre parenthèses quand la ville n'est pas connue : « Née le 27 octobre (Ille-et-Vilaine) : une portée gold, 2 mâles et 3 femelles. Dispo vers le 22 décembre. »
