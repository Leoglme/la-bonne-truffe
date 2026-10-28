import type { FollowUpStatus } from '~/types/api'

export type FollowUpSection = {
  title: string
  statuses: FollowUpStatus[]
  emptyMessage: string | null
}

export type FollowUpReminderChip = {
  label: string
  isUrgent: boolean
}
