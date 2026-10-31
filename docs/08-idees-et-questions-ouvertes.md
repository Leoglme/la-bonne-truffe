# Idées pour plus tard et questions ouvertes

## Questions à trancher par Léo avant ou pendant la V1

Tranchées le 28/10/2026 (détail dans `01-cadrage.md`) : autres couleurs ignorées, sexe indifférent, pas de plafond de prix, départements 35, 56, 22, 29, 44, 53, 49, 72, 85, pas de notification native Windows, Tailwind v4 + Nuxt UI, adresse `contact@dibodev.fr`. **Relevé de la Centrale Canine** : sur le PC de Léo, par le `curl` du système, puisque Cloudflare refuse le client Python même depuis sa connexion (`02-sources.md`). Léo : « tu peux exécuter des commandes sur mon PC ». **Domaines** : `la-bonne-truffe.dibodev.fr` pour le dashboard et `api.la-bonne-truffe.dibodev.fr` pour l'API, déployés comme DevLeadHunter (`11-deploiement.md`).

Restent ouvertes : aucune pour l'instant.

Tranchée le 29/10/2026 : **le relevé de la Centrale Canine une fois l'API sur le VPS** (jalon 5). Les serveurs étant tous refusés (`02-sources.md`), l'app Windows, lancée avec Windows et cachée dans la zone de notification, la relaie dès qu'un PC est allumé ; PC éteints, ses portées attendent le rallumage et les autres sources continuent (`11-deploiement.md`).

Tranchée le 29/10/2026 : **les annonces « Type Cocker Spaniel Anglais » de Chiots de France** (cockers sans papiers et croisements mêlés) sont relevées en non LOF, et le critère « Pedigree LOF », sur « Obligatoire » par défaut, décide si elles s'affichent (`04`).

## Idées V1.5 (après que ça tourne)

- **Temps de route** réel (« à 1 h de chez toi ») à la place de la distance à vol d'oiseau, et une position pour les élevages que seules Chiens de France ou Chiots de France donnent (code postal à géocoder).
- **Page de l'élevage sur la Centrale Canine** (`u_breeder_site`) : le SIREN, la ville et le site de l'éleveur (Chiens de France, Chiots de France) sont affichés depuis le 30/10/2026 ; reste le lien vers sa page SCC.
- **Lien Leboncoin préconstruit** (recherche sauvegardée) et **lien chien.com** par race, pour un coup d'œil manuel depuis l'app.

## Idées V2 (si l'outil marche pour Léo)

- **LOF Select** pour enrichir les parents : généalogie, cotations détaillées, résultats de santé si publiés.
- **Instagram** : lire les publications d'une liste de comptes professionnels d'éleveurs par l'API officielle (« Business Discovery »), avec un compte professionnel relié à une page Facebook. Un test d'une dizaine de minutes dira si c'est possible pour un usage personnel (`02`).
- **Sites d'éleveurs** : relire une fois par jour la page « portées » des quelques éleveurs qui la tiennent à jour (quatre repérés le 29/10/2026 dans les départements du profil) et prévenir quand elle change. Utilité modeste : ces pages suivent souvent la Centrale Canine.
- **chien.com** en source de plus.
- **Multi-races** dans l'interface (le modèle le permet déjà) : un profil par race, un onglet par profil.
- **Version publique** : comptes, abonnements, alertes par e-mail. Risques notés : scraper à l'échelle expose aux conditions d'utilisation et au droit des bases de données de la SCC (les conditions de Whoof et de Cœur de Cocker encadrent aussi la reprise de leurs annonces, `02`), Cloudflare peut durcir, modèle économique faible (un adoptant n'a besoin de l'outil qu'une fois). L'angle qui vaudrait quelque chose : les portées **à naître**, être prévenu avant tout le monde. En attendant, l'inscription est fermée et chaque tentative est gardée (`signup_requests`) : elles diront si d'autres adoptants veulent l'outil avant d'ouvrir (`SIGNUP_ENABLED=true`).
- **Côté éleveur** : une page pour les éleveurs qui veulent être prévenus des adoptants en attente d'une couleur dans leur département.

## Noms de rechange

Le Truffier (« il déniche les portées comme un chien truffier »), À vue de truffe, Truffe & Papiers (clin d'œil aux papiers LOF), Le Truffomètre.

## Phrases d'accroche notées

- « Déniche la bonne portée avant tout le monde. »
- « La Bonne Truffe est à l'affût. On te prévient dès qu'une portée gold pointe sa truffe. » (notification de bienvenue)

## Système éleveurs (maquette du 31/10/2026, à valider)

Léo veut chercher un éleveur par son nom (vu sur Facebook, par exemple), ouvrir sa fiche, voir ses portées et le suivre pour être prévenu. Deux propositions en maquette sur https://claude.ai/artifact/643WfARUJfuo6c3qS6actc : **A**, un onglet Éleveurs (liste classée par chance d'une portée gold, recherche avec suggestions, fiche, tiroir Suivre, ajout à la main) ; **B**, la recherche depuis l'accueil (portées et éleveurs mêlés) et les éleveurs suivis dans le Suivi. Les données viennent de l'annuaire SCC, du Spaniel Club, des fiches chien et des sites d'éleveurs Chiens de France (`02`, § vérifié le 31/10/2026). Léo a validé le principe de l'annuaire SCC et de celui du club.
