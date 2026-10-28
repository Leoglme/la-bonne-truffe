# Idées pour plus tard et questions ouvertes

## Questions à trancher par Léo avant ou pendant la V1

Tranchées le 28/10/2026 (détail dans `01-cadrage.md`) : autres couleurs ignorées, sexe indifférent, pas de plafond de prix, départements 35, 56, 22, 29, 44, 53, 49, 72, 85, pas de notification native Windows, Tailwind v4 + Nuxt UI, adresse `contact@dibodev.fr`. **Relevé de la Centrale Canine** : sur le PC de Léo, par le `curl` du système, puisque Cloudflare refuse le client Python même depuis sa connexion (`02-sources.md`). Léo : « tu peux exécuter des commandes sur mon PC ».

Restent ouvertes :

1. Le nom de domaine et le sous-domaine sur le VPS.
2. **Le relevé une fois l'API sur le VPS** (jalon 5). L'app Windows de Léo, lancée au démarrage dans la zone de notification comme celle de DevLeadHunter, relèvera chaque heure avec le même `curl` et enverra les pages à l'API, qui fera le reste : regroupement, correspondance, notifications. Le worker du VPS ne doit pas relever la Centrale Canine : son image Docker n'a pas `curl`, il échouerait et déclencherait l'alerte « source en panne ». Les portées n'arrivent que quand le PC est allumé.
3. **Les annonces « Type Cocker Spaniel Anglais » de Chiots de France.** La loi réserve le nom d'une race aux chiens LOF : le site range sous ce titre tous les autres, cockers sans papiers et croisements mêlés, sans moyen sûr de les distinguer. Le collecteur les écarte pour l'instant. Le cadrage dit pourtant qu'une annonce non LOF reste visible en « acceptable » : faut-il les montrer quand même, en sachant qu'un croisement y passera pour un cocker ?

## Idées V1.5 (après que ça tourne)

- **Temps de route** réel depuis chez Léo (géocodage des codes postaux + distance routière approximative), affiché sur les cartes comme dans la maquette (« à 1 h de chez toi »), à la place du rang du département.
- **Confirmation de couleur en un geste** depuis le détail après un appel (« C'était noir et feu »), qui remonte le match.
- **Coordonnées de l'éleveur** : afficher le téléphone et le SIREN de la Centrale Canine, bouton d'appel direct, lien vers la page de l'élevage.
- **Lien Leboncoin préconstruit** (recherche sauvegardée) et **lien chien.com** par race, pour un coup d'œil manuel depuis l'app.
- **Rappels** du suivi poussés en notification (« Rappeler De Kerlann aujourd'hui »).
- **Galerie** : toutes les photos de toutes les sources d'une même portée.

## Idées V2 (si l'outil marche pour Léo)

- **LOF Select** pour enrichir les parents : généalogie, cotations détaillées, résultats de santé si publiés.
- **Club de race** (Spaniel Club Français) : liste des éleveurs sélectionnés, portées recommandées.
- **chien.com** en quatrième source.
- **Multi-races** dans l'interface (le modèle le permet déjà) : un profil par race, un onglet par profil.
- **Version publique** : comptes, abonnements, alertes par e-mail. Risques notés : scraper à l'échelle expose aux conditions d'utilisation et au droit des bases de données de la SCC, Cloudflare peut durcir, modèle économique faible (un adoptant n'a besoin de l'outil qu'une fois). L'angle qui vaudrait quelque chose : les portées **à naître**, être prévenu avant tout le monde.
- **Côté éleveur** : une page pour les éleveurs qui veulent être prévenus des adoptants en attente d'une couleur dans leur département.

## Noms de rechange

Le Truffier (« il déniche les portées comme un chien truffier »), À vue de truffe, Truffe & Papiers (clin d'œil aux papiers LOF), Le Truffomètre.

## Phrases d'accroche notées

- « Déniche la bonne portée avant tout le monde. »
- « La Bonne Truffe est à l'affût. On te prévient dès qu'une portée gold pointe sa truffe. » (notification de bienvenue)
