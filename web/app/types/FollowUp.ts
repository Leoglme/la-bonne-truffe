import type { FollowUpStatus } from '~/types/api'

export type FollowUpSection = {
  title: string
  statuses: FollowUpStatus[]
  emptyMessage: string | null
  caption: string | null
  areCardsDimmed: boolean
}

export type FollowUpReminderChip = {
  label: string
  isUrgent: boolean
}
