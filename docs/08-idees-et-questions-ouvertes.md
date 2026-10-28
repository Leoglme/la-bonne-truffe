# Idées pour plus tard et questions ouvertes

## Questions à trancher par Léo avant ou pendant la V1

Tranchées le 28/10/2026 (détail dans `01-cadrage.md`) : autres couleurs ignorées, sexe indifférent, pas de plafond de prix, départements 35, 56, 22, 29, 44, 53, 49, 72, 85, pas de notification native Windows, Tailwind v4 + Nuxt UI, adresse `contact@dibodev.fr`.

Restent ouvertes :

1. Le nom de domaine et le sous-domaine sur le VPS.
2. La collecte Centrale Canine depuis le VPS : à vérifier avant le déploiement (Cloudflare refuse l'IP d'un conteneur cloud, voir `02-sources.md`). Si le VPS est refusé aussi, faire tourner le relevé sur le PC de Léo (un sidecar dans l'app Tauri, comme le scraper de DevLeadHunter) ou passer par Playwright.

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
