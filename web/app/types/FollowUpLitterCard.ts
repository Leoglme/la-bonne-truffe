import type { FollowUpCard } from '~/types/api'

export type FollowUpLitterCardProps = {
  followUp: FollowUpCard
  isNoteShown: boolean
}

export type FollowUpLitterCardEmits = {
  (event: 'open', litterId: number): void
}
