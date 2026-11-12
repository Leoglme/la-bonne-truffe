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

## 28 octobre (nuit) : déploiement sur le VPS

- Sous-domaines `la-bonne-truffe.dibodev.fr` et `api.la-bonne-truffe.dibodev.fr` créés et pointés vers le VPS, certificats certbot posés. Demande : les pipelines et les confs nginx « comme DevLeadHunter ».
- **Même mécanique que DevLeadHunter, sans Docker** : l'API et le worker en services systemd dans un venv, le dashboard en SSR sous pm2, nginx devant ; ports 8030 et 5630. La base SQLite vit hors du dossier que chaque déploiement remplace. Le VPS tourne sous Debian 12 : les contrôles de l'API passent sous Python 3.11, comme lui.
- **Pas de Centrale Canine sur le VPS** : depuis la connexion du PC, le `curl` de Linux (OpenSSL, comme celui de Debian) reçoit `403` avec les en-têtes qui passent avec celui de Windows. Le worker du VPS ne relève donc que Chiens de France et Chiots de France (`COLLECT_SKIPPED_SOURCES`) ; la page Sources affiche la Centrale Canine « Pas encore relevée » (`11-deploiement.md`).
- **Contrôles avant chaque déploiement** : ruff, mypy et pytest pour l'API, Prettier, ESLint et vue-tsc pour le web ; une pull request ne déploie jamais. L'installeur Windows signé est publié en release GitHub à chaque changement du web, comme DevLeadHunter.

## 29 octobre : annonces sans papiers et chiots encore disponibles

- **Annonces « Type Cocker » de Chiots de France** : demande de n'afficher que des portées LOF par défaut, avec un réglage pour choisir LOF obligatoire, préféré ou peu importe, les notifications suivant ce choix. Ce réglage existait déjà (« Pedigree LOF » dans Critères) mais n'avait rien à trier : ces annonces sont désormais relevées en non LOF, le critère passe à « Obligatoire » par défaut, et les profils restés sur « Préféré » y passent aussi (`04`).
- **`availability_change`** : la doc le disait impossible faute de source, mais Chiens de France et Chiots de France donnent les chiots encore disponibles depuis le jalon 4. Validé : une portée suivie qui en propose moins le dit dans le récap du soir, à chaque baisse (`04`).
- **Inscription fermée par défaut** : l'app sert d'abord à un seul utilisateur. L'écran « Créer un compte » reste, mais une tentative est gardée (prénom et adresse, sans mot de passe), affiche « C'est noté ! » et part en push au compte du `.env` : l'inscription ne s'ouvrira (`SIGNUP_ENABLED=true`) que si d'autres personnes se montrent intéressées (`05`).

## 29 octobre (nuit) : la Centrale Canine relayée par les PC

- **Tests depuis des serveurs** : le VPS, l'hébergement o2switch et deux runners GitHub Actions, dont un Windows avec le `curl.exe` accepté depuis le PC, reçoivent tous `403` de Cloudflare (`02`). Changer le User-Agent n'y ferait rien, et contourner la protection est exclu.
- **Demande** : que l'app tourne cachée dans la zone de notification sur les deux PC, démarrée avec Windows, et relève la Centrale Canine dès qu'un PC est allumé, sans fenêtre de navigateur ; PC éteints, les autres sources continuent seules, chaque source restant indépendante.
- **Fait** : l'API donne à l'app les pages à lire, l'app les lit avec le `curl.exe` de Windows et les renvoie, l'API fait le relevé habituel. Un seul PC relaie à la fois, au plus une fois toutes les 55 minutes (`02`, `05`, `11`).

## 29 octobre (matin) : premier relais refusé, demande depuis le téléphone, ménage

- **Premier « Relever maintenant » depuis l'app v0.1.9** : la Centrale Canine renvoie `403`, `cf-mitigated: challenge`, et le même `curl.exe` lancé à la main depuis le PC est refusé aussi (09 h 47), alors qu'il passait à 00 h 34. Le relais a fait ce qu'il devait : une page lue, refusée, arrêt, échec inscrit. L'app envoie désormais les en-têtes dans l'ordre du collecteur qui avait marché le 28/10, au lieu d'un ordre qui changeait à chaque requête.
- **Demande** : un bouton de relevé aussi sur le téléphone. Fait : « Demander un relevé » sur le web et le téléphone, qu'un PC allumé exécute à sa vérification suivante, dans les 5 minutes ; la ligne d'une source en échec dit aussi quand elle a réussi pour la dernière fois.
- **Ménage** : supprimés le brief de départ (`00`), le prompt de la première session cloud (`09`), et `docker-compose.yml` avec le `Dockerfile` de l'API, que ni le VPS ni les workflows n'utilisent.

## 29 octobre : deux sources de plus et deux badges

- **Recherche de sources** : plus de cinquante sites passés en revue, avec Facebook et Instagram. Les gros volumes sont fermés, par leur protection ou leurs conditions (Leboncoin, chien.com, Facebook) ; l'idée des alertes e-mail de chien.com est écartée. Restent deux petites sources propres, Whoof et Cœur de Cocker, et deux informations déjà à portée de main (`02`).
- **Fait** : Whoof et Cœur de Cocker relevés chaque heure (`02`, `05`). Dans le détail d'une portée, deux chips : la santé des parents, tirée de leurs cotations à la Centrale Canine selon la grille du Spaniel Club Français, et « Membre du Spaniel Club Français », que les portées de la Centrale Canine donnent déjà (`02`, `06`).
- **Écarté** : relire chaque semaine la liste des membres du club par le relais de l'app Windows, inutile puisque les portées portent l'information ; les flux RSS payants des pages Facebook, hors des conditions de Meta et fragiles.

## 29 octobre (fin de matinée) : le navigateur de l'app prend le relais

- **Question** : pourquoi la Centrale Canine s'ouvre dans Firefox et Chrome sur le PC, mais refuse le `curl` du relais ? Parce que Cloudflare y lance une vérification JavaScript que les navigateurs passent et que `curl` ne sait pas exécuter. Rappel : DevLeadHunter lit ses pages protégées avec un vrai Chrome piloté en arrière-plan.
- **Décision** : quand Cloudflare refuse `curl`, l'app lit les pages dans une fenêtre cachée de son propre navigateur (WebView2). Pas de script qui masque l'automatisation, pas de proxy, pas de réponse à une vérification qui demande une personne : la lecture échoue alors après 30 secondes.
- **Essai depuis le PC, à 10 h 33** : `curl` refusé (`403`), le navigateur caché lit la page en 4 secondes (`200`, JSON complet) (`02`).

## 31 octobre : les éleveurs et plus de données (jalon 6)

- Léo demande des idées pour trouver son chiot. Retenu : l'éleveur comme objet (carnet, liste d'attente, suivi), la couleur par les parents, plus de données et de photos par portée. Il valide l'annuaire de la Centrale Canine et celui du Spaniel Club, et demande « les chiots un par un, le sexe, la couleur, les photos » et de regarder Chiens de France.
- **Enquête** (`02`) : l'annuaire SCC des éleveurs a un JSON par département ; la fiche d'une portée liste les chiots inscrits et donne l'identifiant LOF Select des parents ; la fiche d'un chien donne sa couleur exacte, sa cotation, ses tests de santé dont le locus E ; les sites d'éleveurs hébergés par Chiens de France donnent les photos, les futures portées, chaque chiot avec son statut, et les reproducteurs avec leur couleur. Pas de photo côté SCC.
- **Maquette** « Éleveurs » (`06`) : deux propositions, Léo retient la A (un onglet), valide tous les écrans et rappelle que le cœur « suivre » reste en haut à droite, jamais dans la barre du bas ; la maquette couvre iPad, iPhone et desktop.
- Décisions et modèle : `01`, `03`, `04`, `05`. Léo : « je te laisse faire tout ce que tu m'as dit ».
- **Livré le soir même** : les trois sources de la Centrale Canine enchaînées dans le relais de l'app Windows (portées, annuaire des éleveurs et du Spaniel Club, fiches des portées et des chiens), les sites d'élevage Chiens de France relevés chaque matin, la couleur attendue d'une portée déduite des parents (deux parents gold : portée gold, classée préférée), les chiots inscrits et leurs sexes, la mère rattachée à son élevage, l'API `/breeders` (liste, recherche par phrase puis par mots, fiche, suivi avec ses alertes et ses notes, ajout à la main), les alertes de suivi (saillie et naissance poussées une fois, photos et annonces dans le récap du soir, rappel), et l'onglet Éleveurs du web sur les trois formats (`05`). Sur le VPS, `COLLECT_SKIPPED_SOURCES` liste les trois sources relayées (`11`). Tests : 300 côté API, les écrans et la présentation côté web.
- **Premier essai de Léo** : « Demander un relevé » sur l'annuaire ne faisait rien de visible. Cause : la demande ne forçait que les portées, l'annuaire et les fiches n'étaient pris que s'ils étaient dus, et l'app Windows s'arrêtait après six allers-retours alors que les trois sources en demandent jusqu'à huit, laissant le relais verrouillé dix minutes. Corrigé : une demande (depuis l'app ou le téléphone) enchaîne les trois sources quel que soit leur dernier relevé, l'app suit le relais jusqu'au bout et n'envoie que les pages lues depuis l'appel précédent, et la page Sources dit « Relevé terminé » ou « Rien à relever ».
- **Deuxième essai** : « Relever maintenant » sur l'annuaire démarre, mais l'app Windows n'acceptait de lire que les adresses sous `/api/breed/` : les pages du club, des portées et des chiens étaient refusées (« Adresse refusée »), le relais s'arrêtait net et restait verrouillé dix minutes. Corrigé : liste d'adresses élargie côté Rust, une page refusée renvoyée à l'API comme échouée, et l'avancement du relais affiché sous chaque source relayée (`05`).
- **Photos** : Léo trouve l'app trop pauvre en images. Décidé et fait le soir même : le mini-site Centrale Canine de chaque élevage (`/<slug>`, slug de l'annuaire) donne une couverture et une galerie, relevées une fois par mois par une quatrième source relayée `scc_sites` (`02`, `03`, `05`) ; la carte et la fiche d'un éleveur montrent la couverture et la galerie, et une portée sans photo montre la couverture de son élevage.
- **Troisième essai** : « Un autre PC relève la Centrale Canine en ce moment » sur chaque carte, même après avoir tout relancé. Le verrou du relais restait posé dix minutes après un relais mort, et un relais légitime de l'autre PC bloquait toute demande. Corrigé : relais muet depuis deux minutes repris par l'appel suivant, pages renvoyées toutes les 40 secondes, et « Relever maintenant » qui attend l'autre PC jusqu'à dix minutes au lieu de renvoyer un message (`05`).

## 1er novembre : les liens des élevages

- Léo veut plus de données, de chiots et d'images, et les liens Facebook et Instagram des élevages ; il reste dans les départements autour de l'Ille-et-Vilaine et refuse Google Places. Vérifié (`02`) : le site du Spaniel Club Français est sa section de la Centrale Canine, déjà relevée ; Chiots de France est déjà relevé ; les sites d'éleveurs « tous pareils » sont ceux de Chiens de France, déjà relevés ; les sites d'annonces (Vivastreet, ParuVendu, Wamiz, Ouest-France) n'ont rien de plus ou refusent les robots ; les fiches chien de la SCC et des mini-sites n'ont pas de photo.
- **Livré** : le relevé des mini-sites lit aussi leur document « general » : les comptes Facebook, Instagram et YouTube d'un élevage (`03`), affichés dans « Vu sur » sur sa fiche, et « mon autre site », qui donne le site Chiens de France d'un éleveur connu seulement par l'annuaire, relevé ensuite chaque matin pour ses photos et ses portées (`05`). Les mini-sites déjà lus la veille sont relus une fois pour leurs liens (migration `reset_scc_site_readings_for_links`).
- **Relevés en direct** : sur l'iPad, « Demander un relevé » ne chargeait pas, et aucun appareil ne voyait un relevé lancé ailleurs. Léo veut que le PC continue de relayer, et que les boutons de l'iPad et du PC chargent en même temps dès qu'un relevé tourne quelque part. Fait : l'API dit ce qui tourne (`GET /sources/activity`), la page Sources la lit toutes les 3 secondes, un relevé du serveur lancé à la main tourne en arrière-plan, et l'app Windows vérifie toutes les 15 secondes si un relevé est demandé (`05`, « Relevés en direct »).

## 1er novembre : les étoiles d'un site d'élevage

- Léo suit la portée « Du Mont de la Chenaie » (Sarthe, née le 29/10). Le site de l'élevage donne 4 ou 5 étoiles aux parents, l'app « Confirmé » (cotation 1) ; il pense que les données de l'élevage ne sont pas alignées sur la Centrale Canine.
- **Vérifié** (`02`) : la Centrale Canine cote les deux parents à 1 partout (liste des portées, fiche de la portée, fiches LOF Select, pages publiques), et l'app affiche cette valeur. Les étoiles de Chiens de France ne sont pas une cotation : elles comptent les générations d'ancêtres saisies sur le site (4 pour le père, 6 pour la mère, jusqu'à 7 pour d'autres chiens de l'élevage). Rien à corriger dans le code.

## 1er novembre : les liens de l'app Windows

- **Signalé** : dans l'app Windows, « Vu sur Centrale Canine » n'ouvre rien ; sur l'iPhone et l'iPad, le même lien ouvre la page.
- **Cause** : les liens vers d'autres sites sont des `<a target="_blank">`, et la fenêtre WebView2 de l'app jette toute demande de nouvelle fenêtre quand aucun gestionnaire n'est posé (code de wry 0.57). Un lien sans `target` aurait, lui, emmené la fenêtre hors de l'app.
- **Fait** : dans l'app Windows seulement, un clic ou un clic molette sur un lien `http` ou `https` vers un autre site l'ouvre dans le navigateur par défaut, par `tauri-plugin-opener` limité à ces deux protocoles : « Vu sur » d'une portée et d'un élevage, site de l'élevage, reproducteurs, Plans, Google Maps et Waze, bouton du bas quand il mène à l'annonce ou au site (`05`). Rien ne change sur le web, l'iPhone et l'iPad, ni pour « Appeler l'éleveur ». Vérifié : `cargo check`, test vitest, lint et typecheck.

## 1er novembre : suivre une portée suit son élevage

- Léo : « quand je suis dans Portée et que je suis une portée, que ça suit aussi l'éleveur, au lieu de devoir suivre une portée, puis aller sur l'éleveur et suivre l'éleveur ».
- **Fait** : une portée qui entre dans le suivi fait suivre son élevage, s'il est connu et pas encore suivi, avec les réglages de départ du tiroir « Suivre cet élevage » ; un élevage déjà suivi ne change pas. Changer ensuite le statut, le rappel ou les notes de la portée ne fait pas revenir un élevage retiré, et « Ne plus suivre » la portée laisse l'élevage suivi (`04`). Le cœur de la fiche de l'élevage et le filtre « Suivis » de l'onglet Éleveurs le montrent aussitôt, sans recharger l'app. Les portées déjà suivies ont fait suivre leur élevage une fois (migration `follow_breeders_of_followed_litters`).

## 1er novembre : les fiches sur ordinateur

- **Demandé** : sur l'app Windows, le détail d'une portée (ouvert depuis le Suivi) et la fiche d'un éleveur (ouverte par « Voir la fiche de l'élevage ») reprenaient la mise en page de l'iPad, avec du vide à droite sur un écran de 1920 px, et le tri montait du bas dans un tiroir. Léo veut des écrans pensés pour l'ordinateur, très épurés, et une maquette avant le code.
- **Maquette** (`06`, canevas « La Bonne Truffe · Desktop ») : deux colonnes, ce qu'on lit à gauche et une carte d'appel à droite ; la fiche d'un éleveur sur le même gabarit ; le tri dans une fenêtre au centre ou dans un menu. Léo valide tout, préfère la fiche avec photos (même mise en page) et retient la fenêtre au centre.
- **Livré** : à partir de 1280 px, les deux fiches passent sur deux colonnes centrées (1240 px au plus), le retour nomme l'écran d'où l'on vient, les photos forment une mosaïque, le numéro de l'éleveur s'affiche en entier avec « Copier », et « Trier les portées » s'ouvre dans une fenêtre au centre de l'écran ; rien ne change sur l'iPhone et l'iPad (`06`). Vérifié dans le navigateur à 1440 et 1920 px, sur iPad et sur iPhone ; tests vitest, lint et typecheck.
- **Premier essai** : Léo réunit les liens d'action à droite. « Vu sur » passe sous la carte d'appel, et la carte « Éleveur » prend toute la largeur à gauche, comme les parents ; sur la fiche d'un éleveur, « Vu sur » se range entre l'appel et « Mon suivi » (`06`).
- **Les tiroirs** : sur captures, Léo veut que tous s'ouvrent en fenêtre au centre sur ordinateur, comme le tri, et plus larges quand ils ont beaucoup à montrer, pour ne pas faire défiler une colonne étroite. Fait : le partage et le choix de l'app de cartes en fenêtre étroite, le suivi d'une portée et « Suivre cet élevage » en fenêtre large ; rien ne change sur téléphone et iPad (`05`, `06`). Sur captures, Léo refuse une colonne de droite dans ces fenêtres larges : tout se range de haut en bas, deux éléments par ligne (le statut et le rappel, les alertes, les deux boutons), et la note passe dessous.

## 1er novembre : les sites d'élevage

- Léo, sur l'élevage de la portée qui l'intéresse : un système « le plus automatisé, le plus épuré possible » qui récupère le site de l'élevage, ou à qui l'on colle son adresse, et qui en tire les photos des chiots, les dates manquantes, les photos du père et de la mère. Il demande aussi d'où venait le lien Facebook : du menu de son site Chiens de France, pas de la Centrale Canine.
- **Maquette** (`06`, canevas « La Bonne Truffe · Sites d'élevage ») : la fiche d'un éleveur au site relié, le tiroir « Ajouter un lien » (site Chiens de France, autre site), une portée avec ses parents en photo et ses chances de gold, les photos des chiots arrivées sur iPhone. Léo valide la maquette et les six pistes proposées.
- **Livré** :
  - le relevé du matin trouve tout seul le site Chiens de France d'un élevage dans les listes régionales des éleveurs (même code postal, même nom), lit « Chiots nés chez nous » (les portées de l'année : le rythme, et les portées gold que seul le site connaît dans « Ses couleurs ») et les comptes du menu du site (`02`, `05`) ;
  - « + Ajouter un lien » sous « Vu sur » : un site Chiens de France est lu tout de suite puis chaque matin, un compte Facebook, Instagram ou YouTube prend sa place, un autre site donne les comptes de son bas de page ; « Vu sur » dit d'où vient chaque compte et quand le site a été relu (`05`, `06`) ;
  - la génétique du gold : `LocEm-…` se lit comme le locus E, un parent né d'un chien de la famille du gold est porteur, et la part des chiots gold (un sur deux, un sur quatre) passe dans la raison du score, sur la carte de la portée de la fiche d'un éleveur, et dans « Les chances de gold » du détail (`03`, `04`) ;
  - les parents d'une portée en photo (la photo du chien du site à la même puce), les reproducteurs avec les parents des portées en cours d'abord et leur cotation en mots, « Les chiots » (photo, sexe, disponible et prix, réservé, vendu) et le badge « NOUVELLES PHOTOS » le jour où elles arrivent et le lendemain (`06`).
- **Vérifié** : dans le navigateur sur une copie de la base locale, l'ajout du vrai site de l'élevage, lu en une minute (36 chiens, 29 avec photo, 7 portées de l'année, la page Facebook) ; la fiche et le détail d'une portée sur iPad, iPhone et à 1440 px ; la fenêtre « Ajouter un lien » sur ordinateur. Faute de fiches Centrale Canine des parents dans la base locale, les photos des parents et « Les chances de gold » y ont été vus sur deux fiches simulées. Tests pytest et vitest, lint et typecheck.
- **La casse de l'affixe** : le nom d'un élevage changeait de casse avec la dernière source lue (« Du Clos de l'Élevage » à la Centrale Canine, « Du Clos De L'Élevage » sur son site). Retenu : l'écriture de la Centrale Canine ; une autre source n'écrit plus que l'affixe d'un élevage qui n'en a pas (`03`). Un élevage déjà touché reprend la casse de la Centrale Canine au prochain passage de l'annuaire ou de ses portées.

## 1er novembre : le site de l'élevage de la Sarthe

- **Constat** : sur les captures de Léo, l'élevage de la portée « Du Mont de la Chenaie » montrait l'illustration du cocker au lieu de photos. Son site Chiens de France (`fonddelachenaie`) ne suit pas son affixe, et ni un mini-site Centrale Canine ni une annonce du site principal ne le donnait à l'app (`02`).
- **Vérifié** : la lecture des listes régionales d'éleveurs, livrée le même jour, le relie au relevé du matin. Sur la vraie liste des Pays de la Loire, sa fiche porte les mêmes mots et le même code postal que son nom d'élevage à la Centrale Canine.
- **Corrigé** : les listes de « Provence-Alpes-Côte d'Azur » et de « La Réunion » n'étaient jamais lues, faute de la bonne adresse (404). Elles prennent maintenant celles des listes de chiots du site (`provence-alpes-cote-dazur`, `reunion`). Tests pytest, ruff et mypy.

## 1er novembre : des pages entières sur ordinateur, et plus rien d'écrasé

- **Demandé** : sur captures, trois affichages écrasés. Sur la fiche d'un élevage, la carte d'une portée (la pastille « Noir ou Noir et feu » cassée sur deux lignes, le nom coupé) et « Ses reproducteurs » (les tests ADN dans une colonne étroite, à côté de la cotation) ; dans l'onglet Éleveurs, les filtres et le tri qui passent à la ligne à côté du volet de droite. Ce volet disparaît sur ordinateur : une carte de Portées ou d'Éleveurs ouvre la page entière, comme le Suivi, l'iPhone et l'iPad. Tout vérifier à plusieurs tailles d'écran.
- **Fait** :
  - plus de volet de droite : une carte ouvre la fiche, « Retour » ramène la liste là où on l'avait laissée, et l'entrée de la barre latérale la reprend en haut (`05`, `06`) ;
  - sur la carte d'une portée, la pastille de couleur et les sexes passent à la ligne d'un bloc, sans se casser ; à l'ordinateur, les portées et les reproducteurs de la fiche d'un élevage font 380 px de large au moins (une colonne jusqu'à 1536 px, deux au-delà) ;
  - un reproducteur montre sa cotation à côté de « Lice » ou « Étalon », son nom en entier, puis ses tests ADN sur toute la largeur de la carte, sans couper un code à son tiret ni commencer une ligne par un point ;
  - les filtres et le tri des éleveurs se rangent sur deux lignes jusqu'à 1280 px, et la grille des éleveurs passe à quatre colonnes à partir de 1536 px, comme celle des portées ;
  - le nom d'un élevage passe à la ligne au lieu d'être coupé (recherche et liste sur iPhone), comme sur les maquettes.
- **Vérifié** : toutes les pages à 390, 820, 1024, 1280, 1440 et 1920 px, avec un relevé automatique des textes coupés, des pastilles sur deux lignes et des débordements ; le retour à la position de la liste à 1440 px et sur iPhone ; tests vitest, lint et typecheck. Les reproducteurs, leurs tests ADN et les chances de gold ont été vus sur des données simulées, que la base locale n'a pas.

## 1er novembre : les logos de « Vu sur » et la surveillance des sites d'élevage

- **Demandé** : un logo automatique sur chaque lien de « Vu sur » d'un élevage (Centrale Canine, Chiens de France, son site, Facebook, YouTube…). Puis, le site de l'élevage de la Sarthe ajouté (`fonddelachenaie.chiens-de-france.com`) : vérifier qu'un site ajouté donne les photos de l'élevage, du père, de la mère et des chiots, et le surveiller une ou deux fois par jour, pour que la portée du 29/10/2026 (deux femelles, un mâle), encore absente de ses pages « chiots disponibles » et « portées à venir », se complète d'elle-même quand elle y paraîtra, avec une notification à chaque nouveauté.
- **Constaté** (lecture réelle du site le 01/11 au soir, par le collecteur de l'app) : le site est lu en entier (36 chiens dont la mère Rillette et le père Samy, chacun avec sa photo ; 14 chiots de deux portées d'août, réservés ou vendus, quatre photos chacun ; les sept portées de l'année ; la page Facebook). La portée du 29/10 n'est encore sur aucune page ; le jour où elle paraîtra, ses annonces rejoindront la portée de la Centrale Canine (même mère, naissances à moins de 30 jours d'écart). Le site était déjà relu chaque matin, mais une nouvelle annonce ou de nouvelles photos n'arrivaient que dans le récap du soir.
- **Fait** :
  - le logo de chaque site dans « Vu sur » (`06`) ;
  - les sites d'élevage relus à 6 h 40 et à 18 h 40 ; une nouvelle annonce ou de nouvelles photos sur une portée d'un élevage suivi partent en push tout de suite (« Nouvelle annonce · … », « Nouvelles photos · … »), avec « Annonce » et « Photos » dans la cloche ; une portée n'envoie qu'une notification par relevé ; seule une photo jamais vue sur l'annonce compte ; le premier relevé d'un site n'envoie rien (`04`, `05`).
- **Vérifié** : tests pytest (toute la suite) et vitest, lint, mypy et typecheck ; les logos sur iPhone, iPad, à 1440 et à 1920 px ; la cloche sur iPhone et à 1440 px, avec des notifications simulées.

## 1er novembre : prévenu le jour même

- **Demandé** : être prévenu le jour même où l'éleveur met la portée qui intéresse (celle du 29/10, un mâle et deux femelles) sur son site, dans ses chiots disponibles ou ses portées à venir, sans attendre la Centrale Canine ni Chiots de France ; et une notification tout de suite quand un chiot d'une portée suivie est réservé. « Faut pas hésiter à m'envoyer des notifications. Ça me dérange pas d'être un peu spam. »
- **Constaté** : les chiots disponibles et les portées à venir d'un site hébergé par Chiens de France paraissent aussi dans la liste régionale du site principal, relue chaque heure, qui rattache l'annonce à l'élevage de la Centrale Canine par son affixe et son département ; le relevé des sites ne passait qu'à 6 h 40 et 18 h 40.
- **Fait** : les sites des élevages suivis sont relus chaque heure de 8 h 55 à 22 h 55, en plus des deux relevés de tous les sites ; une portée qu'un élevage suivi met sur son site part en push dans l'heure (« Nouvelle annonce · … »). Un chiot réservé ou vendu sur une portée suivie part en push à chaque baisse (« Plus que 2 chiots · … ») ; dans Critères, le réglage « Naissance d'une portée suivie » devient « Portée suivie » (« Sa naissance et chaque chiot réservé, tout de suite ») et, coupé, renvoie ces baisses au récap du soir ; la cloche les montre avec « Réservé » (`04`, `05`).
- **Vérifié** : tests pytest (toute la suite) et vitest, lint, mypy et typecheck ; Critères et la cloche sur iPhone, avec des notifications simulées.

## 2 novembre : des photos pour les élevages et les portées

- **Demandé** : faire le tour de l'API et des données, trouver le plus d'images possible pour les portées et les élevages, beaucoup étant sans photo ; les ajouter à la main d'abord, puis automatiser ce qui peut l'être pour les prochains.
- **Constaté** (copie de la base de production du 01/11 au soir) : 32 cartes d'élevage sur 397 avaient une photo, et 10 portées actives sur 22. Les 12 portées sans photo venaient toutes de la Centrale Canine, qui n'a de photo ni sur ses portées ni sur ses chiens, chez des élevages sans site connu. Les 36 « galeries » Centrale Canine étaient les mêmes 16 photos de bergers islandais : le document `api/dogs` de chaque mini-site renvoie la page d'un autre élevage. Le rattachement aux sites Chiens de France par les listes régionales, livré la veille, n'avait pas encore tourné ; il en relie 46 d'un coup.
- **Fait** :
  - la galerie d'un mini-site Centrale Canine se lit sur sa page d'accueil ; les fausses galeries sont effacées et les mini-sites relus (`02`, `05`) ;
  - le rattachement aux sites Chiens de France reconnaît aussi un affixe placé ailleurs par la liste, et une fiche au nom d'une personne (« Mr Jean Dupont ») ; une page qu'un site renvoie vers une autre race compte comme absente, et une image sans fichier (« …/portees/ ») n'est plus une photo (`05`) ;
  - le site propre d'un élevage est lu une fois pour la photo qu'il met en avant, chaque heure et tout de suite à « Ajouter un lien » ; la carte d'un élevage et ses portées sans photo d'annonce prennent la photo de ses sites (`05`, `06`) ;
  - à la main : recherche web sur les 172 élevages les plus utiles (une portée dans l'app, une portée depuis 2025, ou un affixe), puis deux sites Chiens de France, deux sites d'élevages de cockers et cinq pages Facebook ou Instagram (`add_breeder_links_found_by_hand`). Les élevages dont les sites ne montrent plus que d'autres races n'en reçoivent pas ;
  - une photo qui ne se charge plus laisse place à l'illustration, ou aux initiales sur la tuile d'un élevage.
- **Vérifié** : sur une copie de la base de production, les migrations puis les relevés réels des sites Chiens de France (59 sites, aucun en échec), des mini-sites Centrale Canine (8 vraies galeries) et des sites des élevages donnent 71 cartes d'élevage sur 397 avec une photo, et 18 portées actives sur 22. Un échantillon des 38 nouvelles photos montre des cockers des élevages eux-mêmes. Le repli d'une photo cassée vu dans le navigateur. Tests pytest et vitest, lint, mypy et typecheck.
- **Seconde recherche** (même nuit, une fois le quota de recherches web revenu) : les 75 élevages que la première n'avait pas pu chercher l'ont tous été. Aucun site ne montre de cockers : des élevages d'autres races, des sites morts ou vides. Seules les annonces d'un élevage sans site, sur une portée de cockers d'avril 2026, donnent une photo (`add_more_breeder_links_found_by_hand`). Les autres n'ont aucune page à eux en ligne.
- **Reste** : quatre portées actives sans photo, chez trois élevages sans site trouvé (une page Facebook seulement pour l'un d'eux).

## 2 novembre : la cloche ne s'ouvrait plus

- **Constaté** (capture de l'écran Notifications, « L'API ne répond pas ») : le récap du soir du 01/11 à 19 h portait une ligne d'élevage suivi (« … a ajouté des photos à la portée … »), enregistrée avec l'événement `breeder_new_photos`. La liste de la cloche ne lisait que les événements de portée et répondait 500, sans en-tête CORS, d'où le message.
- **Corrigé** : une ligne de récap qui n'est pas un événement de portée laisse le récap à son texte. Depuis le 01/11 au soir, ces nouvelles d'élevage partent en push et plus dans le récap. Vérifié sur une copie de la base de production (la cloche se reconstruit, 5 notifications) et par un test pytest ; déployé dans la nuit.

## 2 novembre : les plus récentes, et les chiots du site des Vents d'Océan

- **Demandé** (en essayant l'app) : un tri pour voir les nouvelles annonces en premier, « Départ le plus tard » n'en étant pas un ; sur l'élevage des Vents d'Océan (Morbihan), les chiots de la portée « née le 19 octobre », mâles et femelles, réservés ou non, avec leurs photos, comme sur son site et mis à jour tout seuls ; et un lien « Vu sur » qui ouvre la page cocker de son site, pas celle du cavalier King Charles, sa première race.
- **Constaté** : la portée du 19 octobre (Tropik) est une saillie dont la naissance était attendue vers le 19/10 ; le 02/11, la Centrale Canine ne l'a pas déclarée née et le site de l'élevage ne la montre pas : personne ne donne encore ses mâles et ses femelles. Les chiots du site sont ceux de la portée née le 9 août (4 mâles et 2 femelles, tous réservés). Le relevé ne les lisait pas : avec une seule portée en vente, « Chiots disponibles » renvoie droit sur la page de la portée, qui ne lie aucune portée, et chaque chiot n'y a qu'une vignette (`02`). Le site nomme aussi Sentiment comme mère, la Centrale Canine Saphir, dont la saillie tombe 63 jours avant : ses chiots auraient formé une portée à part, sans couleur ni département, au score de 30 %.
- **Fait** :
  - « Les plus récentes » dans le tri : la portée dont la dernière annonce est apparue le plus tard en premier ; une portée connue remonte quand une nouvelle annonce la rejoint (`06`) ;
  - le relevé des sites lit la portée unique par l'adresse canonique de sa page, et la photo en grand derrière chaque vignette (`02`) ; il passe toujours chaque heure pour les élevages suivis, et à 6 h 40 et 18 h 40 pour tous ;
  - une annonce née le même jour que la seule portée de l'éleveur sur une autre source la rejoint, quelle que soit la mère qu'elle nomme, sauf si cette portée porte déjà une annonce de la même source avec une autre mère (`03`) ;
  - « Vu sur », le bouton du bas d'un élevage sans téléphone et la carte « Éleveur » d'une portée ouvrent un site Chiens de France à la page de la race (`02`).
- **Vérifié** : sur une copie de la base locale, le vrai site lu (6 chiots, 5 photos, le site n'en a pas pour la sixième) rejoint la portée du 9 août de la Centrale Canine ; dans le navigateur, « Les chiots » de cette portée et le lien « Vu sur » sur iPhone, le tri sur iPhone et en fenêtre à 1440 px. Tests pytest (toute la suite) et vitest, ruff, mypy, lint et typecheck.

## 2 novembre (soir) : les plus récentes par défaut, les filtres gardés, la recherche, les chiots d'une saillie

- **Demandé** : « Les plus récentes » par défaut ; garder en mémoire les derniers filtres choisis dans toute l'app, pour ne pas les refaire à chaque retour ; une barre de recherche dans Portées, comme dans Éleveurs ; et l'assurance d'être prévenu dans l'heure quand l'élevage des Vents d'Océan mettra sur son site les chiots de la portée de Tropik (attendue vers le 19 octobre), avec leurs photos, leur sexe et leur disponibilité.
- **Constaté** : une saillie déclarée (une date de saillie, pas de naissance) et des annonces de chiots (une naissance, pas de saillie) ne se comparaient jamais. Les chiots qu'un site met en ligne avant que la Centrale Canine déclare la naissance auraient fait une portée à part, et la portée suivie serait restée « à naître ». Les chips de Portées et d'Éleveurs, et le tri des Éleveurs, revenaient à leur valeur de départ à chaque lancement.
- **Fait** :
  - une naissance se compare à celle qu'annonce une saillie, 63 jours après elle, à une semaine près quand les deux nomment la même mère (`03`). Un test rejoue le cas : une saillie suivie, puis le relevé horaire du site de son élevage, qui y met les chiots, la fait naître et envoie une seule notification « Portée née » ;
  - « Les plus récentes » par défaut ; les chips et le tri de Portées et d'Éleveurs restent en mémoire sur l'appareil ; un champ de recherche dans Portées, sur l'élevage, la ville et le département, sans tenir compte des accents (`06`).
- **Vérifié** : dans le navigateur, sur une copie de la base locale, la recherche (un élevage, un département, un mot introuvable) et les filtres de Portées et d'Éleveurs retrouvés après un rechargement, sur iPhone et à 1440 px. Tests pytest (toute la suite) et vitest, ruff, mypy, lint et typecheck.

## 12 novembre : les chiots gold d'un couple gold, et les liens vers le site de l'élevage

- **Demandé** : sur la portée du Cercle de Lallybrock (née le 12 novembre, père et mère gold), dessiner les chiots en gold plutôt qu'avec la tête sombre « couleur à confirmer », puisque l'app dit elle-même que tous les chiots seront gold ; et que le lien du chiot 1 (mâle, 1 600 €) ouvre sa vraie fiche, et la ligne « Chiens de France · 7 annonces de chiots » la liste des sept chiots, au lieu de la liste des cockers des Pays de la Loire.
- **Constaté** : l'élevage ne montre ses chiots que sur son propre site, et le site principal renvoie `/chiot/<n>` à sa liste régionale (et répond 404 pour une saillie dans le même cas) ; il n'y a de page par chiot nulle part, seulement la page de la portée sur le site de l'élevage (`02`).
- **Fait** :
  - un chiot dont l'annonce ne donne pas la couleur est dessiné en gold quand le père et la mère ne transmettent que le gold, la même règle que « Les chances de gold » (`06`) ;
  - le relevé des sites garde la page de chaque annonce sur le site de l'élevage (`listings.breeder_site_page_url`, rempli à la mise en production depuis le dernier relevé de chaque site), que l'app ouvre en priorité : la page de la saillie, ou la page de la portée qui défile jusqu'au numéro du chiot et le surligne (`#:~:text=2211562`) ; « Vu sur » et le bouton « Voir sur Chiens de France » d'un élevage sans téléphone ouvrent la page de la portée, avec tous ses chiots (`02`, `03`).
- **Vérifié** : sur une copie de la base locale, la vraie page de la portée lue comme par le relevé des sites : sept chiots dessinés en gold, chaque lien vers la page de la portée pointée sur son chiot, « Vu sur » vers la page de la portée, à 1440 px ; dans Chrome, le lien du chiot 1 ouvre la page de l'élevage avec « 2211562 » surligné. Tests pytest (toute la suite) et vitest, ruff, mypy, lint et typecheck.

## 12 novembre : le départ annoncé par l'élevage, et les deux prix d'une portée

- **Demandé** : sur la portée du Cercle de Lallybrock, l'app affiche « Départ 7 janv. » et « 1 600 € », alors que l'annonce de l'élevage dit « disponibles à partir du 23/01/2027 », un mâle à 1 600 € et six femelles à 1 650 € : reprendre ce que l'élevage annonce.
- **Constaté** : le départ d'une portée était toujours sa naissance + 56 jours, l'âge légal, et le jour annoncé n'était lu nulle part : ni dans le titre de la page de la portée sur le site de l'élevage, ni dans le bloc « Disponibilité » de la fiche d'un chiot sur le site principal. La chip du prix ne gardait que le plus bas.
- **Fait** :
  - le relevé de Chiens de France lit le jour de départ annoncé, sur le site de l'élevage comme sur le site principal (`listings.available_from`, `02`, `03`) ; le départ d'une portée est ce jour quand ses annonces en donnent un, sinon l'âge légal, qui reste aussi quand le jour annoncé tombe avant lui (`03`). La colonne se remplit au premier relevé qui suit la mise en production ; le tri par départ, le « Il arrive le » du chiot trouvé et les notifications suivent ;
  - la chip du prix écrit « 1 600 à 1 650 € » quand les chiots n'ont pas tous le même prix (`highest_price_cents`, `06`) ; le plafond de prix des critères et le tri « Les moins chères » restent sur le prix le plus bas.
- **Vérifié** : sur une copie de la base locale, le vrai site de l'élevage lu comme par le relevé : sept chiots avec leur départ au 23 janvier, le mâle à 1 600 € et les femelles à 1 650 € ; la page partagée de la portée affiche « Départ vers le 23 janv. » et « 1 600 à 1 650 € ». Tests pytest (toute la suite) et vitest, ruff, mypy, lint et typecheck.

## 12 novembre : les photos des reproducteurs sur les fiches récentes de Chiens de France

- **Demandé** : sur la portée du Cercle de Lallybrock, les parents n'ont pas de photo, et la fiche de l'élevage ne montre aucune photo de ses reproducteurs, alors que leurs fiches Chiens de France en ont (`/chien/1479070` pour la mère, `/chien/1294718` pour le père).
- **Constaté** : le relevé lisait bien les deux chiennes de l'élevage, avec leur puce, mais sans photo : leurs fiches sont sur un gabarit récent, sans l'image principale qu'il cherchait (`02`). La photo d'un parent sur une portée étant celle du chien de même puce sur le site de l'élevage, la mère n'en avait pas non plus. Le père est un cas à part : il appartient à un autre élevage, la page de la portée lie pour lui une fiche sans photo (`/chien/1479210`), et la fiche qui a ses photos (`/chien/1294718`) est un autre enregistrement du même chien, sous un nom écrit autrement et avec un tatouage au lieu d'une puce. Rien ne les relie de façon sûre.
- **Fait** : le relevé lit la photo principale et la galerie des fiches récentes, et garde la photo de la liste quand la page n'en donne aucune ; une migration fait relire, au prochain relevé de chaque site, les chiens enregistrés sans photo (une fiche n'est sinon relue qu'au bout de trente jours).
- **Vérifié** : sur une copie de la base locale, avec les vraies pages du site : les deux chiennes de l'élevage ont sept photos chacune sur la fiche de l'élevage, et la mère a sa photo sur la page partagée de la portée ; le père reste sans photo. Tests pytest (toute la suite), ruff et mypy.
