# Historique des échanges de cadrage

Résumé chronologique des discussions entre Léo et Claude (27 et 28 octobre 2026). Les décisions sont reprises dans `01-cadrage.md` ; ce fichier garde le fil et le pourquoi.

## 27 octobre : le besoin et l'état des lieux

- Léo veut adopter un cocker spaniel anglais et trouve pénible de surveiller Leboncoin, Facebook, Chiens de France, la Centrale Canine et Chiots de France. Il imagine une plateforme qui réunit tout et prévient selon race, sexe, localisation. D'abord pour lui, peut-être publique plus tard. Il demande si ça existe.
- Recherche faite : aucun agrégateur multi-sources avec alertes. chien.com a une alerte e-mail par race et pays, mono-source. Leboncoin a ses recherches sauvegardées. Chiens de France et Chiots de France n'ont ni alerte ni RSS. Les sites de surveillance de pages (Visualping, changedetection.io) sont la seule solution de bricolage.
- **Découverte** : la Centrale Canine expose un JSON public des portées LOF déclarées, avec les portées à naître (saillies). Vérifié dans le navigateur puis en ligne de commande : répond à un simple appel HTTP avec User-Agent de navigateur ; filtres variété et né / à naître côté serveur ; le filtre département attend un identifiant interne (`t_41` pour le 35). 650 portées cocker, 220 gold, 150 à naître, 19 en Ille-et-Vilaine.
- Contexte légal relevé : loi de 2021, SIREN obligatoire dans les annonces, cession à huit semaines.
- Proposition de trois paliers : V0 sans code (recherche Leboncoin + changedetection), V1 outil perso, V2 publique. Léo choisit la **V1 perso** avec critères modifiables (race, région, couleurs : gold préféré, noir et feu accepté, LOF de préférence).

## 27 octobre : la stack

- Léo veut la même chose que ses autres projets (DevLeadHunter, Goupixdex) : Nuxt 4 + Tauri 2, utilisable web, mobile, iOS et Windows. Claude propose d'abord « PWA + serveur Nitro, Tauri en option » ; Léo refuse : Tauri est obligatoire.
- Léo propose aussi une API Python FastAPI comme d'habitude ; accepté, c'est le bon outil pour la collecte (httpx, selectolax, APScheduler, rapidfuzz).
- Claude affirme à tort que les push iOS exigent APNs, un plugin Tauri tiers et un compte Apple payant. Léo le reprend : il le fait déjà gratuitement dans DevLeadHunter. Vérifié dans le code : **Web Push VAPID** (pywebpush côté API, service worker et composable côté web), reçu par l'app web ajoutée à l'écran d'accueil ; le Tauri de DevLeadHunter est desktop seulement, sans plugin de notification. Décision : copier ces briques telles quelles.
- Leçon notée pour la suite : lire le code de Léo avant d'affirmer quoi que ce soit sur ses projets.

## 28 octobre : modèle de données et règle de correspondance

- Modèle en neuf tables (races, variétés, départements, éleveurs, groupes de portées, annonces, changements, profils, matches, suivi, relevés), vocabulaire canonique des couleurs avec confiance, dédoublonnage par SIREN puis téléphone puis affixe + département, dates calculées (gestation 63 jours, cession 56 jours).
- Règle en deux temps : filtres durs, puis palier (préférée, acceptable, ignorée) et score 0 à 100 avec raisons lisibles. Notifications par événements, une seule fois par couple groupe + événement. Récap du soir pour les acceptables. Le cas clé : une portée à naître qui naît fait apparaître les sexes et déclenche un push.
- Léo confirme que tout est clair et demande un nom. Propositions : Flair, Truffe, Nichée, Museau. Léo veut un jeu de mots avec « truffe » : **La Bonne Truffe** retenu (clin d'œil au Bon Coin). Variantes notées : Le Truffier, À vue de truffe, Truffe & Papiers, Le Truffomètre.
- Léo redemande la source « avant les naissances » : c'est bien la Centrale Canine (les saillies déclarées), pas un répertoire à part. LOF Select (pedigrees) noté pour enrichir plus tard.

## 28 octobre : la maquette

- Léo demande une maquette, iPad d'abord, belle et fonctionnelle, avec le skill de design, « pas design d'application IA ».
- **Version 1 rejetée** : paysage, papier et encre, serif Fraunces, rail latéral + liste + volet détail. Verdict de Léo : moche, trop chargé, UX nulle, hors thème chien, et il utilise l'iPad en **portrait**. Il renvoie vers Amidipet et les apps d'adoption, et vers le style de DevLeadHunter pour la sobriété.
- **Version 2 validée** : portrait, crème et corail, Fredoka + Nunito, illustrations de cocker en SVG, tuiles pastel, barre d'onglets, un écran = une idée. Léo : « j'aime bien, je trouve ça vraiment pas mal ».
- Suite demandée et livrée : icône retravaillée (truffe crème sur corail) avec aperçu sur l'écran d'accueil iPhone et bannière de notification ; vraies photos de cockers (Unsplash) avec l'illustration gardée en repli et dans Critères ; déclinaisons iPhone (accueil, détail) et desktop (accueil avec volet).
- Le rendu de la maquette n'a pas été vérifié à l'écran par Claude (règle de l'outil de canevas) ; Léo l'a regardé lui-même.

## 28 octobre : passation

- Léo demande un dossier de markdowns (cadrage, sources, idées, échanges) pour une autre session d'IA, moins coûteuse, qui codera l'application à partir de la maquette. C'est ce dossier.

## 28 octobre : première session de code (jalon 0)

- Léo répond aux questions ouvertes : autres couleurs ignorées, sexe indifférent, pas de plafond de prix, départements 35, 56, 22, 29, 44, 53, 49, 72, 85, pas de notification native sur Windows, adresse `contact@dibodev.fr` (comme DevLeadHunter, lue depuis le `.env`).
- **Styles** : Léo choisit Tailwind v4 + Nuxt UI 4 + icônes Lucide, exactement comme DevLeadHunter, après avoir vérifié son code. Les docs 05 et 06 disaient « pas de Tailwind » : mis à jour. Les couleurs, typographies et rayons de la maquette deviennent des tokens de thème.
- **Logo** : l'icône corail arrondie partout, comme le dit le doc 06 ; la maquette iPad `Main.dc.html` (truffe brune seule) est en retard.
- **Écart avec les docs** : depuis le conteneur cloud de la session, la Centrale Canine répond `403` (challenge Cloudflare sur l'IP, `cf-mitigated: challenge`), même avec le User-Agent de navigateur. Rien n'a été contourné. Les `t_ID` des départements (sauf `t_41`) et l'identifiant « autres couleurs » restent à lire avec `python cli.py scc-sync` depuis une IP acceptée ; la fixture de test du collecteur suit la forme documentée et sera remplacée par un vrai relevé. Détail dans `02-sources.md`.
- **Choix techniques** : TypeScript 5.9 (TypeScript 7 n'expose plus l'API JavaScript dont `vue-tsc` a besoin, et `openapi-typescript` exige TypeScript 5) ; PyJWT au lieu de python-jose ; polices auto-hébergées via `@fontsource`.

## 28 octobre : jalons 2 et 3

- Léo demande de passer aux jalons suivants, avec une intégration de la maquette **au pixel près** sur téléphone, iPad et desktop (logo compris), et un typage très strict côté Python et TypeScript.
- **Typage** : mypy strict sur toute l'API, colonnes en `StrEnum`, options TypeScript plus strictes que `strict`.
- **Jalon 2** : regroupement en portées, matching de `04`, événements, push immédiats, récap du soir, alerte « source en panne », API des critères.
- **Jalon 3** : routes du dashboard (portées, détail, couleurs confirmées, suivi et notes, sources) et écrans Accueil, Détail, Critères, Suivi, Réglages, Sources, historique, comparés écran par écran à la maquette rendue (méthode et écarts dans `06`).

## 28 octobre (soir) : relecture et vraie réponse de la Centrale Canine

- Léo demande de relire le code des jalons 0 à 3, de corriger et d'améliorer les conventions, en plusieurs sessions si besoin.
- **Vraie réponse SCC** relevée depuis la connexion de Léo : la forme écrite le 27/10 était fausse sur plusieurs points. `317` est « autres couleurs » et le gold est `158` ; `is_borned` prend `yes`, `no`, `all` ; les filtres et les coordonnées des éleveurs sont dans le JSON ; les valeurs sont des listes Drupal. Collecteur, seeders, synchronisation des identifiants et tests réécrits sur deux vraies pages anonymisées (détail dans `02-sources.md`).
- **Nouveautés** : une portée en ligne depuis plus de 3 jours n'est plus poussée, pour que le premier relevé ou l'ajout d'un département ne déverse pas des semaines de portées. La fraîcheur part de la date de publication.
- **Premier relevé réel refusé** : depuis le PC de Léo, Cloudflare refuse le client Python sur son empreinte TLS, alors que le navigateur et `curl` passent. Léo laisse le choix : « tu peux exécuter des commandes sur mon PC ». Le collecteur passe donc par le `curl` du système : 85 portées au premier relevé réel, aucun changement au deuxième, aucune notification (rien de publié depuis moins de 3 jours).
- **Front** : cinq défauts corrigés. Re-cliquer « Suivie » effaçait le suivi ; le volet desktop ne s'ouvrait jamais ; une couleur connue s'affichait « à confirmer » ; recocher une région déplaçait ses départements en fin de liste ; le détail d'une portée en erreur n'avait plus de bouton retour. Fins de ligne LF imposées (`.gitattributes`), sans quoi le lint échouait sous Windows.


## 28 octobre (nuit) : jalon 4, Chiens de France et Chiots de France

- Léo : « Vas-y, hésite pas à tout commit sur `main` et à passer à la suite. » La PR n° 1 est mergée dans `main`.
- **Chiens de France** : une liste par race et par région, puis la page de chaque chiot et de chaque portée à venir, dans les chemins que le `robots.txt` autorise. Premier relevé réel : 12 annonces dans les deux régions du profil, dont 7 ont rejoint une portée de la Centrale Canine, par le numéro de portée ou par la date de saillie et la mère.
- **Regroupement** complété : les annonces de chiots d'une même portée, les dates de saillie, la même mère nommée à trente jours près, les titres et l'affixe autour du nom de la mère (`03-modele-de-donnees.md`).
- **Premier relevé d'une source** : il n'envoie plus rien, car les portées à venir de Chiens de France n'ont pas de date de publication et seraient passées pour neuves.
- **Défaut trouvé par les vraies données** : le regroupement ne voyait pas les annonces regroupées un instant plus tôt dans le même passage, l'app ouvrant ses sessions sans écriture automatique et les tests avec. Corrigé, et les tests ouvrent désormais leurs sessions comme l'app.
- **Chiots de France** : la liste France de la race, puis la page de chaque annonce des départements du profil. Pour le cocker, il reprend surtout les portées de Chiens de France. Premier relevé réel : 3 requêtes, 2 annonces d'un éleveur de la Sarthe, qui ont rejoint ses chiots de Chiens de France. Les annonces « Type Cocker Spaniel Anglais » (non LOF) sont écartées en attendant une décision (`08`).
- **Deux défauts trouvés en ajoutant cette source** : une annonce vue avant la déclaration de la Centrale Canine imposait ses chiots encore disponibles à la place des mâles et femelles déclarés ; un éleveur sans SIREN, téléphone ni affixe (un particulier) aurait été recréé à chaque relevé. Corrigés, chacun avec son test.

## 28 octobre (nuit) : écrans de connexion et d'inscription

- Léo trouve la page de connexion « beaucoup trop simpliste » face au reste de la maquette et demande connexion, inscription et le reste, en maquette d'abord.
- Première version rejetée : formulaire dans une carte blanche, « Pas encore de compte ? » en lien à gauche d'un bouton (« pas logique au niveau UX »), photo à reprendre. Deuxième version validée : le gabarit des autres écrans, champs blancs sur le crème, deux boutons pleine largeur empilés, photos chaudes (`06-maquette-et-design.md`).
- Léo : « Tu peux commit et push sur main sans souci », puis coder toutes les pages ajoutées à la maquette. L'API gagne l'inscription et le mot de passe oublié ; l'inscription reste ouverte par défaut, `SIGNUP_ENABLED=false` la ferme.
