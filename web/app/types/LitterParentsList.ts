import type { LitterDetail } from '~/types/api'

export type LitterParentsListProps = {
  litter: LitterDetail
}

export type LitterParentRole = 'sire' | 'dam'

export type ParentRatingLabels = Record<LitterParentRole, string>

export type LitterParentLine = {
  role: LitterParentRole
  roleLabel: string
  name: string
  rating: number | null
  ratingLabel: string | null
}
