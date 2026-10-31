import type { LitterDetail } from '~/types/api'

export type FollowUpFoundPuppyCardProps = {
  litter: LitterDetail
}

export type FollowUpFoundPuppyCardEmits = {
  (event: 'confirmed' | 'dismissed'): void
}
