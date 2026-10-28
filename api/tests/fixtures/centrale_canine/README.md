# Fixtures Centrale Canine

**Vraies réponses, anonymisées.** `litters_35_page_0.json` et `litters_35_page_1.json` sont les deux pages du
JSON des portées de cocker spaniel anglais en Ille-et-Vilaine (`department=t_41`), relevées le 28/10/2026 avec
`curl` depuis la connexion de Léo (Cloudflare refuse le client Python, voir `docs/02-sources.md`).

La forme, les clés, les types (valeurs en listes Drupal `[1783252800]`, chaînes, booléens), les identifiants
(`n_id`, `n_breeder`, `n_variety`, `t_41`), les dates, les sexes et les cotations sont ceux de la réponse réelle.
Seules les données personnelles ont été remplacées, le dépôt étant public :

- éleveurs (`litters.breeders`) : nom (`ÉLEVEUR A`), affixe (`DU CLOS DE L'ÉLEVAGE A`), SIREN (`000000001`,
  vide quand il l'était), téléphone (`0600000001`), adresse, ville (`SAINT-AUBIN-DU-CORMIER`, `35140`),
  coordonnées (`48.26,-1.40`), site, logo ;
- chiens : noms des parents (`Père de test 1`), numéros LOF des parents (`000000/00001`).

Un même éleveur ou un même chien porte la même valeur de test dans les deux pages. Les identifiants de la Centrale
Canine (`n_id`, `n_breeder`, `url`) sont gardés : ils mènent aux pages publiques des annonces, où l'éleveur publie
lui-même ses coordonnées.

Pour enregistrer de nouvelles pages, avec un client que la Centrale Canine accepte :

```bash
python cli.py collect --save-raw tests/fixtures/centrale_canine/recorded
```

puis anonymiser les mêmes champs avant de les ajouter au dépôt, et consigner dans `docs/02-sources.md` tout écart de
forme ou de type.
