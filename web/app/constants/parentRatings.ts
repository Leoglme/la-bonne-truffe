import type { LitterParentRole, ParentRatingLabels } from '~/types/LitterParentsList'

/** Highest level of the Centrale Canine selection grid. */
export const MAX_PARENT_RATING: number = 6

/** The name of each level of the grid, agreed with the sex of the parent. */
export const PARENT_RATING_LABELS: Record<number, ParentRatingLabels> = {
  1: { sire: 'Confirmé', dam: 'Confirmée' },
  2: { sire: 'Santé testée', dam: 'Santé testée' },
  3: { sire: 'Excellent', dam: 'Excellente' },
  4: { sire: 'Recommandé', dam: 'Recommandée' },
  5: { sire: 'Élite B', dam: 'Élite B' },
  6: { sire: 'Élite A', dam: 'Élite A' },
}

export const PARENT_ROLE_LABELS: Record<LitterParentRole, string> = {
  sire: 'PÈRE',
  dam: 'MÈRE',
}

export const PARENT_RATING_SCALE_NOTE: string = 'Cotation Centrale Canine : confirmé (1) à élite (6).'
