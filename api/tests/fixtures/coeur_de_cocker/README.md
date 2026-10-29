# Fixtures Cœur de Cocker

**Vrai JSON, réduit et anonymisé.** Relevé le 29/10/2026 depuis un PC de développement : `annonces.json` est la réponse de `/wp-json/cdc/v1/adoption/annonces`, que la page d'adoption lit, réduite à quatre annonces sur treize :

- deux chiots d'Ille-et-Vilaine (35) ;
- un chien adulte (`type` à `Senior`) du même département, que le collecteur écarte ;
- un chiot de Gironde (33), hors des départements du profil.

**Une valeur modifiée** : le premier chiot passe de `adopte` à `disponible`, car aucune annonce n'était disponible ce jour-là.

Les données personnelles ont été remplacées : élevages `Élevage de test A`, `B`, `C`, titres et adresses des annonces, photos. Les dates, sexes, robes, statuts LOF, prix et départements sont ceux du vrai JSON.
