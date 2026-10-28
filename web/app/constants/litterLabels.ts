import type { ListingKind, ListingSource, LofStatus, MatchTier } from '~/types/api'

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
}

export const LISTING_SOURCE_LINK_LABELS: Record<ListingSource, string> = {
  centrale_canine: 'Voir sur la Centrale Canine',
  chiens_de_france: 'Voir sur Chiens de France',
  chiots_de_france: 'Voir sur Chiots de France',
}

export const LOF_STATUS_LABELS: Record<LofStatus, string> = {
  lof: 'LOF',
  non_lof: 'Non LOF',
  unknown: 'LOF à confirmer',
}
