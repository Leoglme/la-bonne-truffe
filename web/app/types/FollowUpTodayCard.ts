import type { FollowUpCard } from '~/types/api'

export type FollowUpTodayCardProps = {
  followUp: FollowUpCard
}

export type FollowUpTodayCardEmits = {
  (event: 'open', litterId: number): void
}
