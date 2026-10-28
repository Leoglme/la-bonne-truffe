import type { FollowUpStatus } from '~/types/api'
import type { FollowUpSection } from '~/types/FollowUp'
import type { UiChoiceButtonsOption } from '~/types/UiChoiceButtons'

/** Statuses offered in the follow-up drawer (« new » is only the state before the first choice). */
export const FOLLOW_UP_STATUS_OPTIONS: UiChoiceButtonsOption[] = [
  { value: 'to_contact', label: 'À appeler' },
  { value: 'contacted', label: 'Contacté' },
  { value: 'waiting', label: 'En attente' },
  { value: 'reserved', label: 'Réservé' },
  { value: 'dismissed', label: 'Écarté' },
]

export const FOLLOW_UP_STATUSES: FollowUpStatus[] = [
  'new',
  'to_contact',
  'contacted',
  'waiting',
  'reserved',
  'dismissed',
]

/** Sections of the follow-up screen; dismissed litters are not shown. */
export const FOLLOW_UP_SECTIONS: FollowUpSection[] = [
  { title: 'À appeler', statuses: ['new', 'to_contact'], emptyMessage: null },
  { title: 'En discussion', statuses: ['contacted', 'waiting'], emptyMessage: null },
  {
    title: 'Réservé',
    statuses: ['reserved'],
    emptyMessage: 'Rien pour l’instant. Quand tu réserves ton chiot, il arrive ici avec sa date de départ.',
  },
]
