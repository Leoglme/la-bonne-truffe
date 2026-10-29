import type { LitterDetail } from '~/types/api'

export type LitterParentsListProps = {
  litter: LitterDetail
}

export type LitterParentLine = {
  role: string
  name: string
  rating: string | null
}
