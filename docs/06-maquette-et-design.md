# Maquette et design

Maquette interactive validée par Léo le 28/10/2026 : https://claude.ai/artifact/4uDTwYLUxdssydGN9bhb53

Sources HTML de chaque écran dans `design/mockup/` (format `.dc.html` : le HTML du `<x-dc>` est du HTML ordinaire, les styles sont inline, la logique est en JavaScript dans le bloc `data-dc-script`). Elles servent de référence visuelle exacte : couleurs, tailles, espacements, rayons.

## Les écrans

| Fichier | Format | Contenu |
|---|---|---|
| `Main.dc.html` | iPad portrait 820 × 1180 | Accueil : salutation, carte « née cette nuit », filtres (Toutes, Préférées, À naître), grille de portées deux par ligne, barre d'onglets |
| `Portee.dc.html` | iPad portrait | Détail : photo en tête, retour et cœur, nom, lieu, pastille « 96 % préférée », trois repères (née le, chiots, départ), chips (couleur, LOF, affixe), galerie, « Pourquoi 96 % », parents, « Vu sur », boutons Appeler et Suivre |
| `Criteres.dc.html` | iPad portrait | Race, couleurs (cinq rangées avec mini cocker et niveaux Préférée / Acceptable / Ignorée, les autres repliées), où chercher (régions, départements ordonnés), le chiot (LOF, sexe, à naître), notifications, bouton Enregistrer |
| `Suivi.dc.html` | iPad portrait | Rappel du jour, sections À appeler, En discussion, Réservé, cartes avec photo ou illustration, note du dernier échange, chip de rappel |
| `Icone.dc.html` | 1180 × 900 | L'icône à plusieurs tailles, le logo dans l'app, l'aperçu sur l'écran d'accueil iPhone avec la bannière de notification |
| `iPhoneAccueil.dc.html`, `iPhonePortee.dc.html` | iPhone 390 × 844 | Même structure, une colonne, tuile photo à gauche des cartes |
| `Desktop.dc.html` | 1440 × 900 | Barre latérale à gauche, grille trois colonnes, volet de détail à droite |
| `Connexion.dc.html` | iPad portrait | Connexion : photo du chiot sur le plaid, bannière de notification qui chevauche son bord bas, « Bon retour », e-mail, mot de passe (« Mot de passe oublié ? » à droite du libellé, bouton œil), « Se connecter » puis « Créer un compte » |
| `Inscription.dc.html` | iPad portrait | Créer un compte : photo, trois pastilles qui chevauchent son bord bas (Tes critères, Relevé chaque heure, Prévenu le premier), prénom, e-mail, mot de passe affiché avec jauge de solidité, « Créer mon compte » puis « J'ai déjà un compte » |
| `MotDePasseOublie.dc.html` | iPad portrait | Tuile gold avec l'illustration et une pastille clé, e-mail, « Envoyer le lien » puis « Retour à la connexion » |
| `LienEnvoye.dc.html` | iPad portrait | Photo et pastille enveloppe, adresse rappelée, validité de 30 minutes, conseil « indésirables », « Retour à la connexion », « Renvoyer le lien » désactivé avec compte à rebours, lien « Modifier l'e-mail » |
| `NouveauMotDePasse.dc.html` | iPad portrait | Tuile lilas avec l'illustration noir et feu et une pastille cadenas, mot de passe avec jauge, « Enregistrer et me connecter » puis « Retour à la connexion » |
| `iPhoneConnexion.dc.html`, `iPhoneInscription.dc.html` | iPhone 390 × 844 | Mêmes écrans en une colonne ; la connexion montre l'état refusé (bandeau corail pastel « E-mail ou mot de passe incorrect », bordure corail sur le mot de passe) |
| `DesktopConnexion.dc.html` | 1440 × 900 | Formulaire dans une colonne de 600 px sur le crème, photo et bannière dans une tuile à droite |

Ajoutées au détail d'une portée le 29/10/2026, sans maquette, dans le style de la chip neutre « Élevage avec affixe » : la santé des parents (« Parents testés APR et NF », « Chiots indemnes d'APR et de NF ») et « Membre du Spaniel Club Français ». Comme l'affixe, elles prennent un libellé court dans le volet du desktop et sur iPhone (« Chiots indemnes APR et NF », « Spaniel Club Français »).

## Direction artistique

Mots d'ordre de Léo : **mignon, fun, dans le thème chien, épuré, agréable, pas « design d'application IA »**. Références qu'il a données : l'app Amidipet (fond chaud, titres ronds et gras, corail, vraies photos de chiens) et les apps d'adoption sur Dribbble (grandes tuiles pastel, chiot au centre, très peu de texte, barre d'onglets).

Ce qu'il a **rejeté** : fond papier et encre, serif éditoriale, rail latéral avec liste et volet de détail sur iPad, trop d'informations par écran, tableaux à quatre colonnes.

### Couleurs

| Rôle | Valeur |
|---|---|
| Fond | `#FBF6EE` crème |
| Cartes | `#FFFFFF`, ombre `0 2px 12px rgba(66,43,30,0.06)` |
| Texte | `#2B2420` ; secondaire `#5E4B3F` ; discret `#7A6657` ; libellés `#9A897B` |
| Accent corail (actions, préféré, onglet actif) | `#E2552F` ; texte corail sur clair `#C94A28` ; pastel corail `#FFE3D3` |
| Pastel gold (tuiles, chip gold) | `#FBE7CC` ; texte sur gold `#8A5A14` |
| Pastel lilas (tuile noir et feu) | `#E9E3F2` |
| Pastel neutre (tuile couleur inconnue) | `#EAE2DA` ; chips neutres `#F3EBDF` |
| Vert LOF | `#DCEBD4`, texte `#3E6630` ; pastille « source en ligne » `#4A6B3B` |
| Sombre (filtre actif, bouton secondaire) | `#2B2420` |
| Lignes | `#F0E6D8` |

Pas de dégradé, pas de verre dépoli, pas d'emoji en guise d'icône (les ♂ et ♀ sont du texte, pas des icônes).

Dans le code, ces valeurs sont des tokens Tailwind v4 déclarés dans le bloc `@theme static` de `web/app/assets/css/main.css` : `cream`, `card`, `ink`, `ink-secondary`, `ink-muted`, `ink-label`, `line`, `coral`, `coral-text`, `coral-pastel`, `gold-pastel`, `gold-ink`, `lilac-pastel`, `neutral-pastel`, `chip`, `lof-pastel`, `lof-ink`, `online`. Le corail est aussi décliné en palette `truffe` (50 à 950, 500 = `#E2552F`), couleur `primary` de Nuxt UI. Les rayons (`rounded-card`, `rounded-tile`…) et les ombres (`shadow-card`, `shadow-floating`) y sont aussi.

### Typographie

- **Fredoka** 500 à 700 pour les titres, les noms de portées, les chiffres clés (40 px salutation iPad, 30 à 34 px titres d'écran, 21 à 24 px noms, 20 à 22 px sections).
- **Nunito** 500 à 800 pour tout le reste (16 px corps iPad, 15 px iPhone, 13 à 14 px secondaire, 11 px minimum pour les libellés, jamais en dessous).
- Auto-hébergées via `@fontsource/fredoka` et `@fontsource/nunito` (graisses importées en tête de `main.css`), servies par le build sans appel à Google Fonts. Le module de polices de Nuxt UI est coupé (`ui.fonts: false`), comme dans DevLeadHunter.

### Formes et espacements

- Rayons : cartes 24 à 28 px, tuiles 18 à 22 px, boutons et chips en pilule (999 px), pastille de score ronde.
- Marges latérales : 32 px sur iPad, 20 px sur iPhone, 36 à 40 px sur desktop. Espacement entre cartes 14 à 20 px.
- Cibles tactiles ≥ 44 px partout (boutons, chips de filtre, onglets, interrupteurs 58 × 34).
- Barre d'onglets en bas (iPad et iPhone) : Portées (patte), Suivi (cœur), Critères (curseurs), Réglages (engrenage). Actif en corail et gras. Pas de barre sur l'écran de détail, qui est un écran poussé avec bouton retour.
- Desktop : barre latérale blanche 236 px avec les mêmes entrées plus Sources, grille trois colonnes, volet de détail à droite 400 px.

### Icônes

Les icônes de la maquette sont des SVG dessinés à la main dans le style Lucide (patte pleine quand l'onglet est actif, cœur plein sur Suivi, curseurs, engrenage, cloche, flux, coche, chevrons, épingle, téléphone, lien externe, truffe). Pour que les écrans collent au pixel, elles sont reprises forme pour forme dans `web/app/constants/mockupIcons.ts` et dessinées par `UiMockupIcon` (taille et épaisseur du trait de chaque emplacement de la maquette : 26 px sur iPad, 24 px sur iPhone, 22 px sur desktop, trait 2, 2,2 pour l'onglet actif). Lucide reste disponible via Nuxt UI (`<UIcon name="i-lucide-…">`, embarqué hors ligne pour Tauri) pour toute icône que la maquette ne dessine pas. Pas d'icône seule sans libellé accessible (`aria-label`). Décoratives : `aria-hidden="true"`.

### L'icône de l'app et le logo

`design/icone-app.svg` : carré arrondi corail `#E2552F` (rayon 22,5 % du côté, comme iOS), truffe crème `#FFF3E6` avec deux narines corail et un reflet blanc. Déclinaisons PNG à générer : 1024, 512, 192, 180. Variante claire (fond crème, truffe brune `#2B2420`) pour les contextes sombres.

Dans l'app, le logo = la même icône arrondie, **sans le reflet blanc** de l'icône d'écran d'accueil (comme « Le logo dans l'app » de `Icone.dc.html`), suivie du nom « La Bonne Truffe » en Fredoka 600, **sur tous les écrans** (composant `UiAppLogo`) : 32 px et 19 px sur iPhone, 36 px et 22 px sur iPad, 38 px et 21 px dans la barre latérale desktop, où le nom passe sur deux lignes exactement comme dans `Desktop.dc.html` (la barre fait 236 px). La maquette iPad `Main.dc.html` est en retard sur ce point : elle montre encore une truffe brune seule ; c'est ce document qui fait foi (validé par Léo le 28/10/2026). Dans la bannière de notification iOS, c'est l'icône de l'app qui apparaît.

Les PNG sont générés dans `web/public/icons/` (1024, 512, 192), plus `web/public/apple-touch-icon.png` (180, **carré plein** : iOS arrondit lui-même et noircirait des coins transparents), `icons/icon-maskable-512.png` (carré plein, la truffe tient dans la zone sûre) et `favicon-32x32.png`. Les icônes Windows de Tauri sont dans `web/src-tauri/icons/` (`npx tauri icon`, en ne gardant que celles que `tauri.conf.json` liste : l'installeur est NSIS, pas le Store).

### L'illustration de cocker

`design/illustration-cocker.svg` : tête de cocker en aplats, oreilles longues, museau, truffe, joues rosées. Trois jeux de couleurs (robe, oreilles, museau) : gold `#E9B363 / #CF8F3A / #F3CF95`, noir et feu `#3A2F2A / #2B2420 / #C98A4B`, couleur inconnue `#6B5A50 / #4A3C34 / #B59A86`. Ajouter noir, marron, bleu rouan avec les mêmes formes.

**Règle des visuels** : une portée affiche sa **photo** (première photo de l'annonce) quand elle existe ; sinon l'**illustration** colorée selon la robe, sur une tuile pastel. Les portées à naître ont une tuile à bord pointillé corail. Dans Critères, ce sont toujours les illustrations (une par couleur).

### Les écrans d'authentification

Validés par Léo le 28/10/2026, après une première version qu'il a rejetée (formulaire dans une carte blanche, contenu centré, « Pas encore de compte ? » en lien à côté d'un bouton, photo au fond gris froid). Ce qui en reste comme règles :

- **Le gabarit des autres écrans** : logo en tête, un grand visuel arrondi (photo ou tuile pastel avec l'illustration), titre Fredoka 40 px à gauche, sous-titre, puis le formulaire. Rien n'est centré dans le vide.
- **Pas de carte autour du formulaire** : les champs sont des blocs blancs posés sur le crème, avec l'ombre des cartes, une bordure blanche de 2 px qui passe en corail au focus avec un halo `#FFE3D3`, et passe en corail aussi quand le champ est refusé.
- **Deux boutons pleine largeur empilés** : l'action principale en corail, l'action secondaire juste dessous en contour sombre de 2 px (« Créer un compte », « J'ai déjà un compte », « Retour à la connexion »). Jamais un lien texte à côté d'un bouton.
- **Photos chaudes** : le chiot sur le plaid pour la connexion, le cocker sur le dos pour l'inscription, le cocker à la balle pour le lien envoyé. La photo aux fleurs reste réservée à l'Accueil.
- **Desktop** : le formulaire passe dans une colonne de 600 px à gauche et le visuel remplit une tuile à droite.

## Comportements à reproduire

- **Accueil** : les filtres sont des boutons `aria-pressed`, sous « Les portées » et en trois tiers sur téléphone ; la carte « née cette nuit » ouvre le détail ; les cartes montrent score en %, badge « Nouveau » corail pour ce qui est apparu depuis la dernière consultation, nom, ville + temps de route, chip couleur, sexes. Comme sur Leboncoin, les portées apparues depuis la dernière consultation de la liste passent en tête, puis le séparateur « Tu es à jour » ; sans nouveauté, il s'affiche en haut. La consultation est notée par le compte à chaque ouverture de l'app (`POST /litters/visit`), pas au clic sur une portée : elle vaut pour l'iPhone, l'iPad et le PC.
- **Actualiser** : dans l'app installée, tirer un écran vers le bas depuis son haut recharge l'app, comme Safari le fait dans un onglet.
- **Détail** : le « Pourquoi 96 % » reprend les `reasons` du match en trois à cinq lignes ; « Appeler l'éleveur » compose le numéro (`tel:`) et prend toute la largeur ; le cœur en haut à droite ajoute au suivi avec statut `to_contact`, puis ouvre le tiroir du suivi ; la galerie montre les photos de toutes les sources, et un tap les ouvre en plein écran, où l'on glisse d'une photo à l'autre ; chaque annonce de chiot devient « Chiot 1 », « Chiot 2 », avec son sexe ; un glissement horizontal passe à la portée voisine, dans l'ordre de l'écran d'où l'on vient (Accueil ou Suivi).
- **Critères** : chaque changement passe le bouton en « Enregistrer » corail, l'enregistrement relance une évaluation des matches ; les niveaux de couleur sont des groupes de boutons `aria-pressed` ; les interrupteurs sont des `role="switch"`.
- **Suivi** : statuts `to_contact`, `contacted`, `waiting`, `reserved`, `dismissed`, choisis dans la liste native ; rappel à un jour et une heure, poussé en notification ; rappel du jour en haut ; notes datées, supprimables ; « Ne plus suivre » efface le suivi.
- **Cloche** : historique des notifications, pastille corail quand il y a du nouveau.
- **Réglages** : activer les notifications (avec l'encart « ajoute l'app à l'écran d'accueil » sur iPhone), état des sources, déconnexion.
- **Connexion et inscription** : un refus affiche le bandeau d'erreur au-dessus des champs ; l'inscription mène aux Critères ; le mot de passe oublié montre « Regarde tes e-mails » sans dire si l'adresse existe, avec un renvoi possible après 45 secondes ; le lien reçu ouvre « Nouveau mot de passe », qui connecte directement.

## Accessibilité

Contraste texte ≥ 4,5:1 (le corail `#E2552F` ne porte que du texte blanc en gras ≥ 18 px ; pour du texte courant sur fond clair, utiliser `#C94A28`), focus visible (`outline` corail 3 px), vrais `<button>` et `<a>`, `aria-current="page"` sur l'onglet actif, `prefers-reduced-motion` respecté sur les transitions (200 ms ease-out sur les interrupteurs).

## Fidélité au pixel : comment c'est vérifié

Les maquettes `.dc.html` n'embarquent pas leur moteur de rendu. Pour comparer, chaque écran est rendu à sa taille exacte (820 × 1180, 390 × 844, 1440 × 900) en évaluant le composant de la maquette, puis comparé côte à côte à la même vue de l'app, alimentée par une base de travail contenant les portées fictives de la maquette (jamais commitée). Constats et choix :

- **Écarts dus aux données, voulus** : la maquette affiche un temps de route (« 1 h de route ») qui n'est pas calculé (idée V1.5) ; l'app montre la ville, ou le département quand la source ne donne pas de ville. Les scores sont ceux de l'algorithme, pas ceux inventés de la maquette.
- **Bug de la maquette iPhone** : dans une colonne flex qui défile, la carte « née cette nuit » (`overflow: hidden`) se compresse à zéro de hauteur. Son code montre qu'elle est voulue : l'app l'affiche.
- **`box-sizing`** : la maquette mesure en `content-box`. Un bouton de 54 px avec une bordure de 2 px y fait donc 58 px (« Suivre ») ; l'app reproduit les hauteurs rendues, pas les valeurs écrites.
- **Hauteur de ligne** : le texte hérite de 1,45 sur iPhone et 1,5 à partir de l'iPad, comme la maquette (les tailles Tailwind n'imposent plus leur propre hauteur de ligne).
- **« Pourquoi ce score »** : trois lignes sur iPhone et dans le volet desktop, jusqu'à cinq sur iPad (les raisons les plus fortes d'abord).
- **Desktop** : barre latérale + grille de trois colonnes + volet de détail à partir de 1280 px ; entre 1024 et 1280 px, deux colonnes et l'écran de détail s'ouvre en plein. La barre latérale ajoute Réglages sous Sources (absent de la maquette, nécessaire pour la déconnexion). Les autres écrans et le détail se calent contre la barre latérale, sur 1024 px au plus, au lieu de se centrer.
- Écrans sans maquette (Réglages, Sources, historique des notifications, Critères et Suivi sur iPhone et desktop, inscription et mot de passe oublié sur desktop) : mêmes composants, mêmes cotes que les écrans iPad.
- **Écrans d'authentification** : un seul cadre, `AuthScreen`, en une colonne jusqu'à 1280 px (l'iPad à l'horizontale garde la mise en page de l'iPad), puis le visuel à gauche et le formulaire à droite. Sur ces grands écrans, une photo étirée en paysage sortait zoomée et pixelisée : le visuel devient un panneau crème dégradé où la photo tient dans une carte au format 2:3, entourée sur la connexion et l'inscription de deux photos de décor inclinées. Les pastilles de l'inscription et la notification de la connexion se centrent sous la carte du milieu, comme sur iPad. Sur téléphone, la pastille unique de l'inscription dit « Prévenu même avant la naissance », pour tenir dès 320 px. Les champs sont les `UFormField` et `UInput` de Nuxt UI, habillés dans `app.config.ts`. Le mot de passe est masqué par défaut, contrairement à l'état montré sur l'inscription de la maquette : le trousseau iOS ne propose un mot de passe fort que sur un champ masqué ; le bouton œil l'affiche. « Ce lien ne marche plus » (lien expiré ou déjà utilisé) n'a pas de maquette : tuile neutre, pastille horloge, mêmes boutons. « C'est noté ! » (inscription tentée pendant qu'elle est fermée) non plus : tuile gold, pastille cloche, l'adresse gardée en gras, « Retour à la connexion ».

## Les photos

Cinq photos Unsplash (licence Unsplash : utilisation libre, attribution appréciée), servies par les écrans de connexion depuis `web/public/images/auth/` :

| Fichier | Page Unsplash | Usage |
|---|---|---|
| `chiot-gold-plaid.jpg` | https://unsplash.com/fr/photos/un-chien-brun-allonge-sur-une-couverture-blanche-Nj3E3DJjilQ | connexion |
| `cocker-gold-dos.jpg` | https://unsplash.com/fr/photos/petit-chien-brun-et-blanc-a-poil-long-couche-sur-de-lherbe-verte-G8cB8hY3yvU | inscription, recompressée à 324 Ko |
| `cocker-gold-balle.jpg` | https://unsplash.com/fr/photos/chien-brun-a-poil-long-sur-le-champ-dherbe-verte-pendant-la-journee--7ac4wXLouE | lien envoyé, et décor de la connexion et de l'inscription sur grand écran |
| `chiot-gold-fleurs.jpg` | https://unsplash.com/fr/photos/un-chien-regardant-la-camera-4gRgy5rjFLI | décor de la connexion |
| `cocker-gold-herbe.jpg` | https://unsplash.com/fr/photos/un-chien-cocker-spaniel-est-assis-sur-lherbe-ah1X0SpRlUc | décor de l'inscription, réduite à 800 px de large |

Dans l'application, les photos des portées viennent des annonces ; sans photo, l'illustration de cocker colorée selon la robe.
