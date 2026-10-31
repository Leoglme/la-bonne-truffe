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
`id`, `breed_id`, `breeder_id` (nullable si éleveur inconnu), `birth_date` (nullable), `expected_birth_date` (nullable, calculée), `mating_date` (nullable), `available_from` (calculée), `is_active`, `is_grouping_probable`, `confirmed_colors` (JSON, couleurs confirmées à la main, ajoutée au jalon 2), `confirmed_male_count` et `confirmed_female_count` (nullable, sexes confirmés à la main après l'appel, ajoutés le 30/10/2026 ; ils priment sur les sources), `puppies_available` (nullable, calculée : les chiots encore proposés, ajoutée le 29/10/2026 pour `availability_change`), `first_seen_at`, `last_seen_at`.

### `listings`
Une annonce ou une déclaration, par source. Une ligne par couple `source` + `external_id`.
`id`, `source` (`centrale_canine` | `chiens_de_france` | `chiots_de_france` | `whoof` | `coeur_de_cocker`), `external_id`, `external_url`, `breed_id`, `breeder_id`, `litter_group_id`, `kind` (`litter_born` | `litter_expected` | `puppy_ad`), `lof_status` (`lof` | `non_lof` | `unknown`), `litter_number`, `mating_date`, `birth_date`, `male_count`, `female_count`, `puppies_available` (nullable, depuis les annonces), `variety_source_id`, `colors` (JSON : liste de `{color, confidence}`), `color_text` (texte libre d'origine), `price_cents` (nullable), `department_code`, `zip_code`, `city`, `sire_name`, `sire_rating`, `dam_name`, `dam_rating`, `litter_rating`, `photos` (JSON, URLs), `description`, `published_at` (mise en ligne sur la source, `n_created` pour la SCC), `first_seen_at`, `last_seen_at`, `last_changed_at`, `is_active`, `content_hash`, `raw_json` (instantané brut de la source).

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

### `notifications`
Historique des notifications envoyées, pour l'écran « cloche » et l'idempotence.
`id`, `user_id`, `kind`, `title`, `body`, `url`, `litter_group_id`, `sent_at`, `delivered_count`, `failed_count`.

## Le vocabulaire canonique des couleurs

Même liste pour toutes les sources, en snake_case : `gold`, `noir`, `noir_et_feu`, `marron`, `marron_et_feu`, `bleu_rouan`, `orange_rouan`, `marron_rouan`, `tricolore`, `particolore`, `zibeline`, `inconnue`.

Chaque couleur d'une annonce porte une **confiance** : `certain` (variété SCC non ambiguë, ou texte libre explicite), `ambiguous` (paquet SCC qui couvre plusieurs couleurs), `confirmed` (confirmée à la main par Léo après un appel, elle gagne toujours).

Correspondance SCC pour le cocker anglais (identifiants lus dans `litters.filters.variety` le 28/10/2026) : `158` → `[gold]` certain ; `159` → `[noir, noir_et_feu, marron, marron_et_feu]` ambigu ; `317` « autres couleurs » → `[bleu_rouan, orange_rouan, marron_rouan, tricolore, particolore]` ambigu. Une base seedée avant cette date porte `317` pour le gold : le seeder corrige l'identifiant et les couleurs d'une variété existante, retrouvée par son libellé.

Texte libre (Chiens de France, Chiots de France) : dictionnaire de mots-clés, par exemple « golden », « rouge », « doré », « fauve » → `gold` ; « noir et feu », « black and tan » → `noir_et_feu` ; « chocolat », « foie », « marron » → `marron` ; « bleu rouan », « blue roan » → `bleu_rouan`. Plusieurs couleurs dans une annonce = plusieurs entrées.

Whoof donne les couleurs et les marques de la robe (`blanc`, `noir`, rouané, feu…) : la couleur n'est retenue, certaine, que quand elles en nomment une sans doute (noir rouané → `bleu_rouan`). Cœur de Cocker donne un libellé par chiot (« Bleu rouan », « Bicolore » → `particolore`) ; « Autre » reste sans couleur.

## Le dédoublonnage

**Éleveur** (dans cet ordre, on s'arrête au premier qui matche) : même `siren` ; sinon même identifiant Centrale Canine ; sinon même `phone_e164` ; sinon même `affix_normalized` **et** même `department_code`. Sinon l'annonce garde l'éleveur qu'elle avait au relevé précédent (un particulier sans SIREN, téléphone ni affixe), et une annonce nouvelle crée le sien.

**Portée**, toujours chez le même éleveur et pour la même race, dans cet ordre (`api/services/litter_grouping.py`, règles complétées le 28/10/2026 avec Chiens de France et le 30/10/2026 avec le numéro de saillie) :
1. même `litter_number`, quelle que soit la source ;
2. même `mating_number` sur la même source : la Centrale Canine peut déclarer la naissance sous un nouvel identifiant, le numéro de saillie reste ;
3. pour une annonce de chiot (`puppy_ad`, un chiot par annonce), une autre annonce de chiot de la même source née le même jour de la même mère : Chiens de France publie chaque chiot à part ;
4. une annonce d'une autre source née, ou saillie, à trois jours près ; à trente jours près quand les deux nomment la même mère, qui ne peut pas avoir deux portées à un mois d'écart (deux sources datent souvent la saillie à quelques jours d'écart) ;
5. pour une annonce sans date de naissance, une seule portée candidate vue dans les soixante derniers jours, avec le drapeau `grouping_probable`.

Deux mères nommées différemment ne sont jamais regroupées. Les noms se comparent en minuscules, sans accents ni ponctuation, et l'un peut contenir l'autre : une source ajoute parfois les titres de la mère devant (« CH. ») ou l'affixe de l'élevage derrière. Sinon on crée un groupe.

**Mâles et femelles d'un groupe** : ceux de la portée née déclarée à la Centrale Canine, même quand l'annonce d'une autre source a été vue avant ; sinon ceux qu'une annonce de portée dit encore disponibles (Chiots de France) ; sinon le nombre de chiots de chaque sexe que proposent ses annonces de chiot, un chiot par annonce (Chiens de France). Le prix est le plus bas des annonces actives.

Normalisation de l'affixe : minuscules, sans accents, sans « de », « du », « des », « la », « le », « l' », espaces réduits.

## Les dates calculées

- Gestation : 63 jours. `expected_birth_date = mating_date + 63 j` quand la naissance n'est pas déclarée.
- Cession légale : 56 jours après la naissance. `available_from = birth_date + 56 j`, ou `expected_birth_date + 56 j` (affiché « vers le … »).
- `is_active` passe à faux quand une annonce disparaît de sa source pendant deux relevés de suite, ou quand une portée née a plus de six mois.
