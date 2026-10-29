import type { ListingKind, ListingSource, LofStatus, MatchTier } from '~/types/api'
import type { BreedingQualityChip, LitterInfoChipLabels } from '~/types/LitterInfoChips'

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
}

export const LISTING_SOURCE_LINK_LABELS: Record<ListingSource, string> = {
  centrale_canine: 'Voir sur la Centrale Canine',
  chiens_de_france: 'Voir sur Chiens de France',
  chiots_de_france: 'Voir sur Chiots de France',
  whoof: 'Voir sur Whoof',
  coeur_de_cocker: 'Voir sur Cœur de Cocker',
}

export const LOF_STATUS_LABELS: Record<LofStatus, string> = {
  lof: 'LOF',
  non_lof: 'Non LOF',
  unknown: 'LOF à confirmer',
}

export const BREEDING_QUALITY_CHIP_LABELS: Record<BreedingQualityChip, LitterInfoChipLabels> = {
  affix: { fullLabel: 'Élevage avec affixe', shortLabel: 'Avec affixe' },
  parents_tested: { fullLabel: 'Parents testés APR et NF', shortLabel: 'Parents testés APR et NF' },
  puppies_unaffected: { fullLabel: 'Chiots indemnes d’APR et de NF', shortLabel: 'Chiots indemnes APR et NF' },
  breed_club_member: { fullLabel: 'Membre du Spaniel Club Français', shortLabel: 'Spaniel Club Français' },
}
