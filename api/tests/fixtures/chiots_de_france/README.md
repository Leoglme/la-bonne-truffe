# Fixtures Chiots de France

**Vraies pages, réduites et anonymisées.** Relevées le 28/10/2026 depuis le PC de Léo :

- `listing_france.html` : la liste des cockers de toute la France, réduite à quatre cartes : la portée de l'éleveur A (35), celle d'un éleveur F (72, sans prix), une portée hors des départements du profil (50) et un croisé « Type Cocker Spaniel Anglais » (28) ;
- `ad_486970.html` et `ad_487726.html` : les pages de ces deux portées, réduites aux blocs que le collecteur lit (fiche, informations, parents, liste des photos).

Le balisage (balises, classes, imbrication) est celui des vraies pages. Les scripts, publicités et menus ont été retirés. Les données personnelles ont été remplacées :

- l'annonce 486970 devient la portée 4320820 de l'éleveur A des fixtures Centrale Canine : affixe (`Du Clos de l'Élevage A`), site (`elevage-a.chiens-de-france.com`), SIRET (`00000000100017`), ville (`Saint-Aubin-du-Cormier`, `35140`), naissance le 28/08/2026, parents `Père de test 11` et `Mère de test 12`. Les tests vérifient ainsi qu'elle rejoint cette portée ;
- l'annonce 487726 devient celle d'un éleveur F, absent des autres fixtures : `Du Clos de l'Élevage F`, `elevage-f`, SIRET `00000000600017`, `72000 LE MANS`, parents `Père de test 40` et `Mère de test 41` ;
- la carte hors zone porte l'affixe `Du Clos de l'Élevage G` et la ville `SAINT-LÔ` ;
- les puces, les liens des chiens et toutes les photos (portée, parents, cartes) ont des valeurs de test.

Les identifiants d'annonce gardés mènent aux pages publiques du site, comme pour les autres sources.
