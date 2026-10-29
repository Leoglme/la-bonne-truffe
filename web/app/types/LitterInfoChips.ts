import type { GeneticScreening, LitterDetail } from '~/types/api'

export type LitterInfoChipsProps = {
  litter: LitterDetail
  isInSidePanel: boolean
}

export type BreedingQualityChip = 'affix' | GeneticScreening | 'breed_club_member'

export type LitterInfoChipLabels = {
  fullLabel: string
  shortLabel: string
}
