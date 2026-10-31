# Fixtures des sites d'éleveurs hébergés par Chiens de France

**Vraies pages, réduites et anonymisées.** Relevées le 31/10/2026 depuis le PC de Léo, sur deux sites de cockers (`<slug>.chiens-de-france.com/cocker-spaniel-anglais/…`) ramenés à un seul site de test, `elevage-a.chiens-de-france.com` :

- `litters_to_come.html` : `/saillies`, la liste « Portées à venir » avec deux saillies (28/08/2026 et 14/09/2026), chacune avec ses parents et son lien `/saillie/<id>` ;
- `litters_to_come_empty.html` : la même page sur un site sans saillie (« Aucune portée à venir ») ;
- `litters_for_sale.html` : `/chiots`, la liste « Nos portées » avec deux portées en vente et leur lien `/chiots-a-vendre/<id>`, plus l'encart « Chiots disponibles » dont le lien garde son espace final, comme sur le vrai site ;
- `litter_for_sale_495610.html` : `/chiots-a-vendre/495610`, une portée et ses quatre chiots (un disponible à 1400 €, un mâle réservé, une femelle réservée, un vendu), chacun avec son propre carrousel de photos, puis les parents et le tableau de la portée (code portée, date de naissance, « 18 femelles reproductrices … et 14 portées au cours de l'année écoulée ») ;
- `females.html` et `studs.html` : `/chiens/femelles` et `/chiens/etalons`, la grille des chiens avec leur lien `/chien/<id>`, leur photo en fond et leur état (« Chien à vendre », « Disponible pour saillie ») ;
- `dog_1212400.html` : `/chien/1212400`, la page d'une femelle avec son tableau (Sexe, Couleur, Puce, Inscrit au LOF ?, Cotation, Statut) et ses parents ;
- `home.html` : la page d'accueil de la race, réduite à ses paragraphes de présentation et à leurs photos chargées en différé (`data-original`).

Le balisage (balises, classes, imbrication) est celui des vraies pages. Les scripts, publicités, menus et bandeau de cookies ont été retirés ; les listes de chiens sont ramenées à deux chiens et les carrousels à deux photos. Les données personnelles ont été remplacées par les valeurs de test de l'éleveur A des fixtures Centrale Canine et Chiens de France : affixe (`Du Clos de l'Élevage A`), sous-domaine (`elevage-a.chiens-de-france.com`), noms des chiens (`Chien de test 1`, `Père de test 11`, `Mère de test 12`), puces (`250000000000003`), textes de présentation, et photos (`photo-de-test-N`, dossier `eleveurs/0/0/`). Les photos que le vrai site sert depuis le sous-domaine de l'éleveur restent sur `elevage-a.chiens-de-france.com` ; celles qu'il sert depuis `www.chiens-de-france.com/photo/…` gardent cet hôte.

Les identifiants gardés (portées 495610 et 494507, saillies 495662 et 495668, chiots 2199886 à 2199889, chiens 1212400, 1430047, 1386355 et 1264388, code portée `LOF- 2026024873-2026-13`) mènent aux pages publiques des vrais sites. Le chiot 2199888 et la portée `2026024873` sont ceux des fixtures Chiens de France ; les tests vérifient ainsi que ce collecteur et celui du site principal décrivent la même annonce. Aucune page relevée ne porte la mention « Inscrit sur chiens-de-france.com depuis le … » : `registered_on` reste `None`.

Dans les tests, le site vide (`elevage-b`) est servi avec `litters_to_come_empty.html` et `home.html`, et le site en panne (`elevage-c`) répond 500 à tout.
