import type { FollowUpStatus } from '~/types/api'
import type { UiSegmentedControlOption } from '~/types/UiSegmentedControl'

/** Statuses offered in the follow-up drawer (« new » is only the state before the first choice). */
export const FOLLOW_UP_STATUS_OPTIONS: UiSegmentedControlOption[] = [
  { value: 'to_contact', label: 'À appeler' },
  { value: 'contacted', label: 'Contacté' },
  { value: 'waiting', label: 'En attente' },
  { value: 'reserved', label: 'Réservé' },
  { value: 'dismissed', label: 'Écarté' },
]

const FOLLOW_UP_STATUSES: readonly FollowUpStatus[] = [
  'new',
  'to_contact',
  'contacted',
  'waiting',
  'reserved',
  'dismissed',
]

/**
 * Whether a value emitted by the status control is a follow-up status.
 *
 * @param value - Emitted value.
 * @returns True for a known status.
 */
export function isFollowUpStatus(value: string): value is FollowUpStatus {
  return (FOLLOW_UP_STATUSES as readonly string[]).includes(value)
}
