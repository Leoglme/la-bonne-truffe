import type { NotificationKind } from '~/types/api'

export type NotificationHeaderLineProps = {
  kind: NotificationKind
  sentAt: string
  isUnread: boolean
}
