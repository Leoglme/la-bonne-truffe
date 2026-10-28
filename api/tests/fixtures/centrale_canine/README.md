# Fixtures Centrale Canine

**Fixtures synthétiques, pas des enregistrements.** Le 28/10/2026, la Centrale Canine a refusé l'IP du
conteneur cloud de la session de développement (challenge Cloudflare, voir `docs/02-sources.md`) : aucune
réponse réelle n'a pu être enregistrée.

- `litters_35_page_0.json` reprend **la forme documentée** de la réponse (`cache_tags`, `breed`,
  `litters.count`, `litters.node` groupé par qualité d'élevage `1`, `2`, `3`, champs `n_*`). Les noms
  (`TEST Père A`…), numéros (`LOF-TEST-…`) et identifiants (`9000001`…) sont des valeurs de test explicites.
  Certains champs sont volontairement en nombres, d'autres en chaînes : le type réel n'est pas connu.
- `breed_page_selects.html` reproduit les filtres `<select>` de la page ; seules les valeurs `t_41`, `317`
  et `159` sont documentées, les autres sont des marqueurs `TEST`.

À remplacer par de vrais relevés dès qu'une IP acceptée est disponible :

```bash
python cli.py collect --save-raw tests/fixtures/centrale_canine/recorded
```

puis adapter les tests et consigner dans `docs/02-sources.md` tout écart de forme ou de type.
