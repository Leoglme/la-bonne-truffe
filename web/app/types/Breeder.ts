import type { BreederFilter, BreederFollowStatus, BreederSort } from '~/types/api'

export type BreederChipTone = 'neutral' | 'gold' | 'coral' | 'green' | 'lilac'

export type BreederChip = {
  label: string
  tone: BreederChipTone
}

export type BreederLitterStatusTone = 'hot' | 'normal' | 'inactive'

export type BreederLitterStatusLine = {
  text: string
  tone: BreederLitterStatusTone
}

export type BreederStat = {
  label: string
  compactLabel: string
  value: string
}

export type BreederColorShareSlice = {
  label: string
  percent: number
  swatch: string
  littersCount: number
}

export type BreederSeenOnLink = {
  key: string
  label: string
  description: string
  href: string | null
}

export type BreederFilterOption = {
  key: BreederFilter
  label: string
}

export type BreederSortOption = {
  key: BreederSort
  label: string
}

export type BreederFollowStatusOption = {
  value: BreederFollowStatus
  label: string
}

export type BreederNotificationSettingKey =
  'notify_new_mating' | 'notify_birth' | 'notify_new_photos' | 'notify_ignored_colors'

export type BreederNotificationSetting = {
  key: BreederNotificationSettingKey
  label: string
  helper: string
}
