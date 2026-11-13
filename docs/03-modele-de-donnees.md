# Modèle de données

SQLAlchemy côté API, SQLite dans un seul fichier (un seul utilisateur, quelques milliers de lignes au plus). Toutes les tables métier portent `user_id` et des horodatages `created_at` / `updated_at` en UTC naïf (convention DevLeadHunter : l'API renvoie de l'UTC sans suffixe Z, le front affiche en heure locale).

## Les tables

### `users` et `push_subscriptions`
Copiées de DevLeadHunter : un utilisateur avec mot de passe hashé et jeton JWT, et `litters_visited_at` (nullable : dernière consultation de la liste des portées, sur n'importe quel appareil) ; les abonnements Web Push (`endpoint`, `p256dh`, `auth`, `user_agent`, `created_at`) avec purge automatique des endpoints morts (404/410).

### `breeds`
Catalogue des races avec leurs identifiants par source.
`id`, `name_fr` (« Cocker spaniel anglais »), `slug`, `scc_slug` (`cocker-spaniel-anglais`), `scc_breed_id` (237), `chiens_de_france_id`, `chiots_de_france_id`, `whoof_id` (`cocker-spaniel-anglais`), `coeur_de_cocker_id` (`Cocker Anglais`), `is_active`.

### `breed_varieties`
Les paquets de couleur tels que chaque source les connaît.
`id`, `breed_id`, `source`, `source_variety_id` (ex. `158`), `label` (« rouge et doré »), `covered_colors` (JSON, liste de couleurs canoniques), `is_ambiguous` (vrai si le paquet couvre plusieurs couleurs).

### `departments`
`code` (« 35 »), `name`, `region`, `scc_term_id` (`t_41`). Seedée depuis une liste région → départements ; les `scc_term_id` viennent de `litters.filters.department` du JSON SCC (74 relevés le 28/10/2026), et le relevé complète ceux qui manquent (`02-sources.md`).

### `breeders`
L'ancre du dédoublonnage.
`id`, `display_name`, `affix` (affixe, nullable), `affix_normalized`, `siren` (unique, nullable), `phone_e164` (nullable), `email`, `zip_code`, `city`, `department_code`, `latitude`, `longitude` (position publiée par la source), `website`, `scc_breeder_id`, `scc_selection_group` (1 sélectionné, 2 avec affixe, 3 sans affixe), `is_breed_club_member` (membre du club de la race d'après les portées de la Centrale Canine, nul tant qu'elle ne liste pas l'éleveur ; ajouté le 29/10/2026), `notes`.

### `litter_groups`
Une portée réelle, vue sur une ou plusieurs sources.
`id`, `breed_id`, `breeder_id` (nullable si éleveur inconnu), `birth_date` (nullable), `expected_birth_date` (nullable, calculée), `mating_date` (nullable), `available_from` (calculée : le jour de départ annoncé, sinon l'âge légal, voir « Les dates calculées »), `is_active`, `is_grouping_probable`, `confirmed_colors` (JSON, couleurs confirmées à la main, ajoutée au jalon 2), `confirmed_male_count` et `confirmed_female_count` (nullable, sexes confirmés à la main après l'appel, ajoutés le 30/10/2026 ; ils priment sur les sources), `puppies_available` (nullable, calculée : les chiots encore proposés, ajoutée le 29/10/2026 pour `availability_change`), `first_seen_at`, `last_seen_at`.

### `listings`
Une annonce ou une déclaration, par source. Une ligne par couple `source` + `external_id`.
`id`, `source` (`centrale_canine` | `chiens_de_france` | `chiots_de_france` | `whoof` | `coeur_de_cocker`), `external_id`, `external_url`, `breeder_site_page_url` (nullable : la page de l'annonce sur le site propre de l'élevage, lue sur ce site, que l'app ouvre en priorité : la page d'une saillie, ou celle d'une portée pointée sur le numéro d'un chiot par `#:~:text=<n>` ; le site principal de Chiens de France n'a pas de page pour les annonces que seul ce site montre, `02`), `breed_id`, `breeder_id`, `litter_group_id`, `kind` (`litter_born` | `litter_expected` | `puppy_ad`), `lof_status` (`lof` | `non_lof` | `unknown`), `litter_number`, `mating_date`, `birth_date`, `available_from` (nullable, ajoutée le 12/11/2026 : le jour où l'annonce dit que les chiots peuvent partir, lu sur Chiens de France ; une lecture qui ne le donne pas garde celui d'une lecture précédente), `male_count`, `female_count`, `puppies_available` (nullable, depuis les annonces), `variety_source_id`, `colors` (JSON : liste de `{color, confidence}`), `color_text` (texte libre d'origine), `price_cents` (nullable), `department_code`, `zip_code`, `city`, `sire_name`, `sire_rating`, `dam_name`, `dam_rating`, `litter_rating`, `photos` (JSON, URLs), `description`, `published_at` (mise en ligne sur la source, `n_created` pour la SCC), `first_seen_at`, `last_seen_at`, `last_changed_at`, `is_active`, `content_hash`, `raw_json` (instantané brut de la source).

### `listing_changes`
Historique des champs qui bougent, pour les événements (« les sexes sont apparus », « le prix a changé »).
`id`, `listing_id`, `field`, `old_value`, `new_value`, `changed_at`.

### `search_profiles`
Les critères, modifiables dans l'app. Un profil actif pour Léo, mais plusieurs possibles.
`id`, `user_id`, `name`, `is_active`, `breed_ids` (JSON), `department_codes` (JSON, **ordonné** du plus proche au plus loin), `include_expected_litters` (bool), `sex_preference` (`male` | `female` | `any`), `lof_preference` (`required` | `preferred` | `any`), `color_preferences` (JSON : `{ "gold": "preferred", "noir_et_feu": "acceptable", ... }`), `price_max_cents` (nullable), `notify_preferred_immediately` (bool), `notify_acceptable_in_digest` (bool), `digest_hour` (19), `notify_birth_of_followed` (bool), `max_puppy_age_days` (61 par défaut, nullable : les portées trop anciennes ne sont jamais masquées).

### `listing_matches`
Le verdict d'un groupe de portée face à un profil. Recalculé à chaque relevé.
`id`, `litter_group_id`, `profile_id`, `tier` (`preferred` | `acceptable` | `ignored` | `excluded`), `score` (0-100), `reasons` (JSON : liste de `{text, points}`), `flags` (JSON : `color_to_confirm`, `sex_unknown`, `lof_unknown`…), `computed_at`, `notified_events` (JSON : `{ "new_preferred": "<date>", "born": "<date>" }`).

### `follow_ups` et `follow_up_notes`
Le suivi perso.
`follow_ups` : `id`, `litter_group_id`, `status` (`new` | `to_contact` | `contacted` | `waiting` | `reserved` | `dismissed`), `next_reminder_at` (nullable), `reminder_sent_at` (nullable : heure d'envoi du push du rappel, remise à vide quand le rappel change), `last_contact_at`, `updated_at`.
`follow_up_notes` : `id`, `follow_up_id`, `created_at`, `text`.

### `source_runs`
`id`, `source`, `started_at`, `finished_at`, `status` (`ok` | `error`), `listings_seen`, `listings_new`, `listings_changed`, `error_message`.

### `digest_entries` (ajoutée au jalon 2)
Les événements gardés pour le récap du soir : `id`, `user_id`, `litter_group_id`, `event_kind`, `created_at`, `sent_at` (null tant que le récap n'est pas parti). Une ligne par couple portée + événement.

### `signup_requests` (ajoutée le 29/10/2026)
Les inscriptions tentées pendant qu'elles sont fermées, pour mesurer l'intérêt pour l'app : `id`, `name`, `email` (unique, en minuscules), `requested_at`, `last_requested_at`. Jamais de mot de passe.

### `litter_shares` (ajoutée le 31/10/2026)
Les liens privés d'une portée, ouverts sans compte pendant 30 jours : `id`, `token` (unique, la partie secrète du lien), `user_id`, `litter_group_id` (le lien disparaît avec la portée), `message` (nullable, le mot laissé pour les destinataires), `created_at`, `expires_at` (30 jours après la création).

### `puppy_arrivals` (ajoutée le 31/10/2026)
Le chiot trouvé, une ligne au plus par utilisateur : `id`, `user_id` (unique), `litter_group_id` (nullable, vidé si la portée disparaît), `arrival_on` (le jour où il arrive à la maison), `done_items` (JSON : les clés des préparatifs cochés), `created_at` (le début de la pause des alertes). Reprendre la recherche supprime la ligne.

### `notifications`
Historique des notifications envoyées, pour l'écran « cloche » et l'idempotence.
`id`, `user_id`, `kind`, `title`, `body`, `url`, `litter_group_id`, `sent_at`, `delivered_count`, `failed_count`.

## Le vocabulaire canonique des couleurs

Même liste pour toutes les sources, en snake_case : `gold`, `noir`, `noir_et_feu`, `marron`, `marron_et_feu`, `bleu_rouan`, `orange_rouan`, `marron_rouan`, `tricolore`, `particolore`, `zibeline`, `inconnue`.

Chaque couleur d'une annonce porte une **confiance** : `certain` (variété SCC non ambiguë, ou texte libre explicite), `ambiguous` (paquet SCC qui couvre plusieurs couleurs), `confirmed` (confirmée à la main par Léo après un appel, elle gagne toujours). La variété SCC d'une portée est celle de sa mère (`02`) : même `certain`, elle passe après ce qu'écrivent les annonces et ce que donnent les parents (`04`).

Correspondance SCC pour le cocker anglais (identifiants lus dans `litters.filters.variety` le 28/10/2026) : `158` → `[gold]` certain ; `159` → `[noir, noir_et_feu, marron, marron_et_feu]` ambigu ; `317` « autres couleurs » → `[bleu_rouan, orange_rouan, marron_rouan, tricolore, particolore]` ambigu. Une base seedée avant cette date porte `317` pour le gold : le seeder corrige l'identifiant et les couleurs d'une variété existante, retrouvée par son libellé.

Texte libre (Chiens de France, Chiots de France) : dictionnaire de mots-clés, par exemple « golden », « rouge », « doré », « fauve » → `gold` ; « noir et feu », « black and tan » → `noir_et_feu` ; « chocolat », « foie », « marron » → `marron` ; « bleu rouan », « blue roan » → `bleu_rouan`. Plusieurs couleurs dans une annonce = plusieurs entrées.

Whoof donne les couleurs et les marques de la robe (`blanc`, `noir`, rouané, feu…) : la couleur n'est retenue, certaine, que quand elles en nomment une sans doute (noir rouané → `bleu_rouan`). Cœur de Cocker donne un libellé par chiot (« Bleu rouan », « Bicolore » → `particolore`) ; « Autre » reste sans couleur.

## Le dédoublonnage

**Éleveur** (dans cet ordre, on s'arrête au premier qui matche) : même `siren` ; sinon même identifiant Centrale Canine ; sinon même `phone_e164` ; sinon même `affix_normalized` **et** même `department_code`. Sinon l'annonce garde l'éleveur qu'elle avait au relevé précédent (un particulier sans SIREN, téléphone ni affixe), et une annonce nouvelle crée le sien.

**Portée**, toujours chez le même éleveur et pour la même race, dans cet ordre (`api/services/litter_grouping.py`, règles complétées le 28/10/2026 avec Chiens de France et le 30/10/2026 avec le numéro de saillie) :
1. même `litter_number`, quelle que soit la source ;
2. même `mating_number` sur la même source : la Centrale Canine peut déclarer la naissance sous un nouvel identifiant, le numéro de saillie reste ;
3. pour une annonce de chiot (`puppy_ad`, un chiot par annonce), une autre annonce de chiot de la même source née le même jour de la même mère : Chiens de France publie chaque chiot à part ;
4. une annonce d'une autre source née, ou saillie, à trois jours près ; à trente jours près quand les deux nomment la même mère, qui ne peut pas avoir deux portées à un mois d'écart (deux sources datent souvent la saillie à quelques jours d'écart). Une naissance se compare aussi à celle qu'annonce une saillie, 63 jours après elle, à une semaine près quand les deux nomment la même mère (une gestation dure de 56 à 70 jours), à trois jours sinon : les chiots qu'un élevage met sur son site rejoignent la saillie déclarée à la Centrale Canine avant qu'elle y déclare la naissance (ajouté le 02/11/2026) ;
5. la seule portée de l'éleveur qu'une autre source dit née **le même jour**, quelle que soit la mère qu'elle nomme, avec le drapeau `grouping_probable` : le site d'un élevage peut nommer une autre de ses lices que la Centrale Canine (ajouté le 02/11/2026, site des Vents d'Océan : la portée du 9 août y a pour mère Sentiment, Saphir à la Centrale Canine, dont la saillie tombe 63 jours avant). Une portée qui porte déjà une annonce de la même source nommant une autre mère est une autre portée ;
6. pour une annonce sans date de naissance, une seule portée candidate vue dans les soixante derniers jours, avec le drapeau `grouping_probable`.

Hors du même jour de naissance (règle 5), deux mères nommées différemment ne sont jamais regroupées. Les noms se comparent en minuscules, sans accents ni ponctuation, et l'un peut contenir l'autre : une source ajoute parfois les titres de la mère devant (« CH. ») ou l'affixe de l'élevage derrière. Sinon on crée un groupe.

**Mâles et femelles d'un groupe** : ceux de la portée née déclarée à la Centrale Canine, même quand l'annonce d'une autre source a été vue avant ; sinon ceux qu'une annonce de portée dit encore disponibles (Chiots de France) ; sinon le nombre de chiots de chaque sexe que proposent ses annonces de chiot, un chiot par annonce (Chiens de France). Le prix est le plus bas des annonces actives.

Normalisation de l'affixe : minuscules, sans accents, sans « de », « du », « des », « la », « le », « l' », espaces réduits.

Écriture de l'affixe : celle de la Centrale Canine, qui le délivre. Une autre source n'écrit que l'affixe d'un élevage qui n'en a pas, si bien que le nom ne change plus de casse avec la dernière source lue (01/11/2026).

## Les dates calculées

- Gestation : 63 jours. `expected_birth_date = mating_date + 63 j` quand la naissance n'est pas déclarée.
- Départ : le jour que les annonces de la portée annoncent quand elles en donnent un (le plus tôt de celles encore en ligne, `listings.available_from`), car un élevage garde souvent ses chiots plus longtemps que la loi ne le demande ; sinon la cession légale, 56 jours après la naissance : `available_from = birth_date + 56 j`, ou `expected_birth_date + 56 j`. Un jour annoncé avant l'âge légal est une erreur de saisie : l'âge légal reste. Affiché « vers le … ».
- `is_active` passe à faux quand une annonce disparaît de sa source pendant deux relevés de suite, ou quand une portée née a plus de six mois.

## Jalon 6 : les éleveurs, les chiens et le suivi d'éleveur (31/10/2026)

### `breeders`, colonnes ajoutées
`scc_user_id` (l'`u_id` de l'annuaire, unique nullable), `scc_breeder_number`, `scc_site_slug` (`u_breeder_site`), `logo_url` (`u_user_picture_uri` rendue absolue), `scc_variety_ids` (JSON : variétés produites, toutes races mêlées), `scc_last_litter_at` (`u_last_litter_date`), `is_scc_selected` (`is_selected` de l'annuaire ; `scc_selection_group` reste celui des portées), `scc_directory_seen_at` (dernier passage dans l'annuaire), `chiens_de_france_site_url` (le sous-domaine, lu sur une annonce ou une saillie), `chiens_de_france_registered_on` (« Inscrit sur chiens-de-france.com depuis le … »), `breeding_females_count` et `litters_last_year_count` (« 18 femelles reproductrices … 14 portées au cours de l'année écoulée »), `cover_photo_url`, `scc_site_cover_url` et `scc_site_photos` (JSON, la couverture et la galerie du mini-site Centrale Canine), `scc_site_seen_at` (dernière lecture du mini-site, relu au plus une fois par mois), `website_photo_url` et `website_read_at` (la photo que le site de l'élevage met en avant, et quand il a été lu ; un site est lu une fois), `facebook_url`, `instagram_url` et `youtube_url` (les comptes que le mini-site déclare, que le menu du site Chiens de France donne, ou que Léo colle, en adresses ; un compte retiré d'un site reste connu), `social_link_origins` (JSON : d'où vient chaque compte, `{"facebook": "centrale_canine" | "breeder_site" | "added_by_hand"}` ; celui que Léo colle remplace tout, celui de la Centrale Canine remplace tout sauf le sien, celui d'un site ne comble qu'une place vide), `chiens_de_france_site_seen_at` (dernière lecture du site Chiens de France), `chiens_de_france_litters` (JSON : les portées de l'année de « Chiots nés chez nous », `[{birth_date, sire_name, dam_name}]`, remplacées à chaque lecture de la page), `links` (JSON : liens ajoutés à la main, `{label, url}`), `is_manual` (créé à la main par Léo), `created_by_user_id` (nullable), `search_text` (concaténation normalisée pour la recherche : affixe, nom, ville, code postal, SIREN, téléphone en chiffres, liens).

### `dogs` (nouvelle)
Un chien connu d'une source, parent, reproducteur ou chiot.
`id`, `breeder_id` (nullable : l'élevage qui le présente ou qui l'a fait naître), `source` (`centrale_canine` | `chiens_de_france`), `external_id` (identifiant LOF Select `ws.chien.id`, ou l'`<id>` de `/chien/<id>` sur le site de l'éleveur ; unique par source), `external_url`, `role` (`parent` | `reproducer` | `puppy`), `litter_group_id` (nullable : la portée dont il est le chiot), `name`, `affix`, `full_name`, `sex` (`male` | `female` | `unknown`), `birth_date`, `lof_number`, `identifier` (puce ou tatouage), `color_code` (le code brut de la source, `F.Or.`, « Noire et blanche »), `color` (couleur canonique ou `inconnue`), `rating` (cotation 0 à 6), `health_codes` (JSON : `["FN-1.1", "PRCD-1.1", "LocE-e/e"]`), `e_locus` (`e/e` | `E/e` | `E/E` | null, extrait de `LocE-…` ou de `LocEm-…`, où l'allèle du masque `Em` compte comme `E`), `has_dna_profile`, `sire_external_id` et `dam_external_id` (identifiants LOF Select des parents, nullable), `photos` (JSON), `availability_text` (« Disponible pour saillie », « En vente »), `sire_color_code` et `dam_color_code` (le code couleur brut de ses propres parents, lu sur sa fiche LOF Select : un parent de la famille du gold fait de lui un porteur), `fetched_at`, `created_at`, `updated_at`.

### `litter_groups`, colonnes ajoutées
`sire_dog_id` et `dam_dog_id` (identifiants de lignes `dogs`, nullables, sans contrainte en base : les deux tables se référencent), `expected_colors` (JSON : `[{color, confidence, reason, puppy_odds}]` déduites des parents ; `puppy_odds`, la part des chiots de la couleur, quand les génotypes la donnent), `puppies_detail_fetched_at` (dernière lecture des chiots un par un), `puppies_detail_next_try_at` (prochaine tentative tant que les chiots ne sont pas inscrits). Les chiots inscrits sont les lignes `dogs` de `role = puppy` liées au groupe.

### `breeder_follows` et `breeder_follow_notes` (nouvelles)
`breeder_follows` : `id`, `user_id`, `breeder_id` (unique par utilisateur), `status` (`to_contact` | `contacted` | `waiting` | `deposit`), `notify_new_mating`, `notify_birth`, `notify_new_photos`, `notify_ignored_colors` (booléens, vrai, vrai, vrai, faux par défaut), `next_reminder_at`, `reminder_sent_at`, `last_contact_at`, `created_at`, `updated_at`. Une portée qui entre dans `follow_ups` crée aussi le suivi de son élevage, avec ces valeurs par défaut, quand il n'existe pas (`04`).
`breeder_follow_notes` : `id`, `follow_id`, `created_at`, `text`.

### `breeder_follow_events` (nouvelle)
L'idempotence des alertes d'éleveur : `id`, `follow_id`, `litter_group_id` (nullable), `kind` (`breeder_new_mating` | `breeder_birth` | `breeder_new_photos` | `breeder_new_ad`), `created_at`, `sent_at` (null tant que l'événement attend le récap du soir ; les pushs et les événements non envoyés sont datés tout de suite). Une ligne par couple (suivi, portée, type) ; `breeder_new_photos` se répète quand de nouvelles photos arrivent (une ligne par lot, datée).

### Les couleurs, complément
Une quatrième confiance : **`inferred`**, déduite des parents (`expected_colors`). Elle vaut `certain` pour le palier et le score tant qu'aucune source ne donne la couleur des chiots ; une couleur de chiot inscrit (`certain`) ou confirmée à la main (`confirmed`) la remplace.

Correspondance des codes LOF Select (`ws.chien.couleur`, à compléter au fil des fiches ; le code brut est gardé dans `color_code`) : `F.Or.`, `F.Cl.`, `F.Fo.`, `F.`, `Rou.`, `Gol.` → `gold` ; `Noi.` seul → `noir` ; `Noi. Mar.Fau.`, `Noi. Fau.` → `noir_et_feu` ; `Mar.` seul → `marron` ; `Mar. Fau.` → `marron_et_feu` ; `Ble. Rou.` → `bleu_rouan` ; `Ora. Rou.` → `orange_rouan` ; `Mar. Rou.` → `marron_rouan` ; `Tri.` → `tricolore` ; `Pan.Bla.`, `Bla.` avec une autre couleur → `particolore` ; `Zib.` → `zibeline` ; sinon `inconnue`. Les libellés en clair de Chiens de France (« Noire et blanche », « Golden ») passent par le dictionnaire de mots-clés existant.

Règle du locus E : `e/e` × `e/e` → gold certain, tous les chiots ; `e/e` × `E/e` → gold possible (ambigu : gold et la couleur de l'autre parent), un chiot sur deux ; `E/e` × `E/e` → gold possible, un chiot sur quatre ; `e/e` × `E/E` → pas de gold ; sans test, un parent gold vaut `e/e`, un parent d'une autre couleur dont le père ou la mère a une robe de la famille du gold (gold, rouge, orange ou citron, rouanné ou panaché de blanc) vaut `E/e`, sinon « inconnu » (gold possible si l'autre parent est gold, sans part).
