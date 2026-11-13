import type { DogSex, ListingKind, ListingSource, LofStatus, MatchFlag, MatchTier, PuppyAdState } from '~/types/api'
import type { FrenchGender } from '~/types/FrenchText'
import type { BreedingQualityChip, LitterInfoChipLabels } from '~/types/LitterInfoChips'
import type { SourceRunCountForms } from '~/types/SourceRun'

export const TIER_LABELS: Record<MatchTier, string> = {
  preferred: 'préférée',
  acceptable: 'acceptable',
  ignored: 'ignorée',
  excluded: 'exclue',
}

export const UNEVALUATED_TIER_LABEL: string = 'à évaluer'

export const LISTING_KIND_LABELS: Record<ListingKind, string> = {
  litter_expected: 'déclaration de saillie',
  litter_born: 'déclaration de naissance',
  puppy_ad: 'annonce',
}

export const LISTING_SOURCE_LABELS: Record<ListingSource, string> = {
  centrale_canine: 'Centrale Canine',
  chiens_de_france: 'Chiens de France',
  chiots_de_france: 'Chiots de France',
  whoof: 'Whoof',
  coeur_de_cocker: 'Cœur de Cocker',
  scc_breeders: 'Annuaire des éleveurs (Centrale Canine)',
  scc_sites: 'Sites d’élevage (Centrale Canine)',
  scc_dogs: 'Fiches des chiens (Centrale Canine)',
  chiens_de_france_sites: 'Sites d’élevage (Chiens de France)',
}

export const SOURCE_RUN_COUNT_FORMS: Record<ListingSource, SourceRunCountForms> = {
  centrale_canine: { singularForm: 'portée vue', pluralForm: 'portées vues' },
  chiens_de_france: { singularForm: 'annonce vue', pluralForm: 'annonces vues' },
  chiots_de_france: { singularForm: 'annonce vue', pluralForm: 'annonces vues' },
  whoof: { singularForm: 'annonce vue', pluralForm: 'annonces vues' },
  coeur_de_cocker: { singularForm: 'annonce vue', pluralForm: 'annonces vues' },
  scc_breeders: { singularForm: 'éleveur vu', pluralForm: 'éleveurs vus' },
  scc_sites: { singularForm: 'site lu', pluralForm: 'sites lus' },
  scc_dogs: { singularForm: 'fiche de chien lue', pluralForm: 'fiches de chiens lues' },
  chiens_de_france_sites: { singularForm: 'annonce ou chien vu', pluralForm: 'annonces et chiens vus' },
}

export const LISTING_SOURCE_LINK_LABELS: Record<ListingSource, string> = {
  centrale_canine: 'Voir sur la Centrale Canine',
  chiens_de_france: 'Voir sur Chiens de France',
  chiots_de_france: 'Voir sur Chiots de France',
  whoof: 'Voir sur Whoof',
  coeur_de_cocker: 'Voir sur Cœur de Cocker',
  scc_breeders: 'Voir sur la Centrale Canine',
  scc_sites: 'Voir le site de l’élevage',
  scc_dogs: 'Voir sur la Centrale Canine',
  chiens_de_france_sites: 'Voir le site de l’élevage',
}

export const LOF_STATUS_LABELS: Record<LofStatus, string> = {
  lof: 'LOF',
  non_lof: 'Non LOF',
  unknown: 'LOF à confirmer',
}

export const BREEDING_QUALITY_CHIP_LABELS: Record<BreedingQualityChip, LitterInfoChipLabels> = {
  selected_breeding: { fullLabel: 'Élevage sélectionné', shortLabel: 'Sélectionné' },
  parents_tested: { fullLabel: 'Parents testés APR et NF', shortLabel: 'Parents testés APR et NF' },
  puppies_unaffected: { fullLabel: 'Chiots indemnes d’APR et de NF', shortLabel: 'Chiots indemnes APR et NF' },
  breed_club_member: { fullLabel: 'Membre du Spaniel Club Français', shortLabel: 'Spaniel Club Français' },
}

/** The place of a litter or a breeder while no source gives it. */
export const UNKNOWN_PLACE_LABEL: string = 'Lieu à confirmer'

/** What the breeder card says of a breeder whose kennel name is registered (an affix). */
export const BREEDER_AFFIX_LINE: string = 'Nom d’élevage déposé à la Centrale Canine'

/** How « À confirmer avec l’éleveur » names each unknown fact; the colour has its own section. */
export const MATCH_FLAG_LABELS: Record<MatchFlag, string | null> = {
  color_to_confirm: null,
  sex_unknown: 'les sexes',
  lof_unknown: 'le LOF',
  price_unknown: 'le prix',
  department_unknown: 'le département',
}

/** The sex of the puppy of an ad, when the ad tells it. */
export const PUPPY_SEX_LABELS: Record<Exclude<DogSex, 'unknown'>, string> = {
  male: 'Mâle',
  female: 'Femelle',
}

export const PUPPY_SEX_TEXT_CLASSES: Record<DogSex, string> = {
  male: 'text-male',
  female: 'text-female',
  unknown: '',
}

/** Where the puppy of an ad stands once it is no longer free, agreed with its sex. */
export const PUPPY_AD_STATE_LABELS: Record<Exclude<PuppyAdState, 'available'>, Record<FrenchGender, string>> = {
  reserved: { masculine: 'Réservé', feminine: 'Réservée' },
  sold: { masculine: 'Vendu', feminine: 'Vendue' },
}
