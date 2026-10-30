import type { NotificationKind } from '~/types/api'
import type {
  NotificationChip,
  NotificationChipTone,
  NotificationDayDefinition,
  NotificationIconTile,
} from '~/types/Notification'

export const NOTIFICATION_CHIPS: Record<NotificationKind, NotificationChip> = {
  born: { label: 'Née', tone: 'coral' },
  new_preferred: { label: 'Préférée', tone: 'gold' },
  upgraded: { label: 'Préférée', tone: 'gold' },
  follow_up_reminder: { label: 'Rappel', tone: 'dark' },
  evening_digest: { label: 'Récap du soir', tone: 'neutral' },
  source_down: { label: 'Source', tone: 'neutral' },
  source_silent: { label: 'Source', tone: 'neutral' },
  signup_request: { label: 'Inscription', tone: 'lilac' },
}

export const NOTIFICATION_CHIP_CLASSES: Record<NotificationChipTone, string> = {
  coral: 'bg-coral-pastel text-coral-text',
  gold: 'bg-gold-pastel text-gold-ink',
  dark: 'bg-ink text-cream',
  neutral: 'bg-chip text-ink-secondary',
  lilac: 'bg-lilac-pastel text-ink',
}

/** The tile of a notification about no litter: an icon on a pastel; the other kinds show their litter. */
export const NOTIFICATION_ICON_TILES: Partial<Record<NotificationKind, NotificationIconTile>> = {
  source_down: { iconName: 'i-lucide-rss', tileClass: 'bg-coral-pastel text-coral-text' },
  source_silent: { iconName: 'i-lucide-rss', tileClass: 'bg-coral-pastel text-coral-text' },
  signup_request: { iconName: 'i-lucide-user-plus', tileClass: 'bg-lilac-pastel text-ink' },
}

export const NOTIFICATION_DAY_SECTIONS: NotificationDayDefinition[] = [
  { key: 'today', title: 'Aujourd’hui' },
  { key: 'yesterday', title: 'Hier' },
  { key: 'earlier', title: 'Plus tôt' },
]
