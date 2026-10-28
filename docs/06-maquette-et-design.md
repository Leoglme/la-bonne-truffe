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

Icônes **Lucide** via Nuxt UI (`<UIcon name="i-lucide-paw-print">`, collection `@iconify-json/lucide` embarquée dans le bundle client pour la fenêtre Tauri hors ligne), 22 à 26 px. Barre d'onglets : `paw-print`, `heart`, `sliders-horizontal`, `settings`. Pas d'icône seule sans libellé accessible (`aria-label`). Décoratives : `aria-hidden="true"`. Seuls le logo et l'illustration de cocker restent en SVG inline.

### L'icône de l'app et le logo

`design/icone-app.svg` : carré arrondi corail `#E2552F` (rayon 22,5 % du côté, comme iOS), truffe crème `#FFF3E6` avec deux narines corail et un reflet blanc. Déclinaisons PNG à générer : 1024, 512, 192, 180, 120, 60. Variante claire (fond crème, truffe brune `#2B2420`) pour les contextes sombres.

Dans l'app, le logo = la même icône arrondie à 32 à 38 px suivie du nom « La Bonne Truffe » en Fredoka 600, **sur tous les écrans** (composant `UiAppLogo`). La maquette iPad `Main.dc.html` est en retard sur ce point : elle montre encore une truffe brune seule ; c'est ce document qui fait foi (validé par Léo le 28/10/2026). Dans la bannière de notification iOS, c'est l'icône de l'app qui apparaît.

Les PNG sont générés dans `web/public/icons/` (1024, 512, 192, 120, 60), plus `web/public/apple-touch-icon.png` (180, **carré plein** : iOS arrondit lui-même et noircirait des coins transparents), `icons/icon-maskable-512.png` (carré plein, la truffe tient dans la zone sûre) et `favicon-32x32.png`. Les icônes Windows de Tauri sont dans `web/src-tauri/icons/` (`npx tauri icon`).

### L'illustration de cocker

`design/illustration-cocker.svg` : tête de cocker en aplats, oreilles longues, museau, truffe, joues rosées. Trois jeux de couleurs (robe, oreilles, museau) : gold `#E9B363 / #CF8F3A / #F3CF95`, noir et feu `#3A2F2A / #2B2420 / #C98A4B`, couleur inconnue `#6B5A50 / #4A3C34 / #B59A86`. Ajouter noir, marron, bleu rouan avec les mêmes formes.

**Règle des visuels** : une portée affiche sa **photo** (première photo de l'annonce) quand elle existe ; sinon l'**illustration** colorée selon la robe, sur une tuile pastel. Les portées à naître ont une tuile à bord pointillé corail. Dans Critères, ce sont toujours les illustrations (une par couleur).

## Comportements à reproduire

- **Accueil** : les filtres sont des boutons `aria-pressed` ; la carte « née cette nuit » ouvre le détail ; les cartes montrent score en %, badge « Nouveau » corail pour ce qui est apparu depuis la dernière visite, nom, ville + temps de route, chip couleur, sexes.
- **Détail** : le « Pourquoi 96 % » reprend les `reasons` du match en trois à cinq lignes ; « Appeler l'éleveur » compose le numéro (`tel:`) ; « Suivre » ajoute au suivi avec statut `to_contact` ; la galerie montre les photos de toutes les sources.
- **Critères** : chaque changement passe le bouton en « Enregistrer » corail, l'enregistrement relance une évaluation des matches ; les niveaux de couleur sont des groupes de boutons `aria-pressed` ; les interrupteurs sont des `role="switch"`.
- **Suivi** : statuts `to_contact`, `contacted`, `waiting`, `reserved`, `dismissed` ; rappel du jour en haut ; notes datées.
- **Cloche** : historique des notifications, pastille corail quand il y a du nouveau.
- **Réglages** : activer les notifications (avec l'encart « ajoute l'app à l'écran d'accueil » sur iPhone), état des sources, déconnexion.

## Accessibilité

Contraste texte ≥ 4,5:1 (le corail `#E2552F` ne porte que du texte blanc en gras ≥ 18 px ; pour du texte courant sur fond clair, utiliser `#C94A28`), focus visible (`outline` corail 3 px), vrais `<button>` et `<a>`, `aria-current="page"` sur l'onglet actif, `prefers-reduced-motion` respecté sur les transitions (200 ms ease-out sur les interrupteurs).
