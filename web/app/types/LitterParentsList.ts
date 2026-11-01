import type { CoatColor, LitterDetail } from '~/types/api'

export type LitterParentsListProps = {
  litter: LitterDetail
  isTitleShownOnPhone: boolean
  isInWideLayout: boolean
}

export type LitterParentRole = 'sire' | 'dam'

export type ParentRatingLabels = Record<LitterParentRole, string>

export type LitterParentLine = {
  role: LitterParentRole
  roleLabel: string
  name: string
  color: CoatColor | null
  colorAndGenotypeLine: string | null
  photoUrl: string | null
  rating: number | null
  ratingLabel: string | null
}
