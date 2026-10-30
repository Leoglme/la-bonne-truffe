import type { SentNotification } from '~/types/api'

export type NotificationChipTone = 'coral' | 'gold' | 'dark' | 'neutral' | 'lilac'

export type NotificationChip = {
  label: string
  tone: NotificationChipTone
}

export type NotificationDayKey = 'today' | 'yesterday' | 'earlier'

export type NotificationDayDefinition = {
  key: NotificationDayKey
  title: string
}

export type NotificationDaySection = NotificationDayDefinition & {
  notifications: SentNotification[]
}

export type NotificationIconTile = {
  iconName: string
  tileClass: string
}
