import type { GeneticScreening, LitterDetail } from '~/types/api'

export type LitterInfoChipsProps = {
  litter: LitterDetail
  isInAside: boolean
}

export type BreedingQualityChip = 'selected_breeding' | GeneticScreening | 'breed_club_member'

export type LitterInfoChipLabels = {
  fullLabel: string
  shortLabel: string
}
