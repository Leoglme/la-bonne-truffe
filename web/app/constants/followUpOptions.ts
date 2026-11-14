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

/** Sections of the follow-up screen; dismissed litters come last, greyed, since they left the home list. */
export const FOLLOW_UP_SECTIONS: FollowUpSection[] = [
  { title: 'À appeler', statuses: ['new', 'to_contact'], emptyMessage: null, caption: null, areCardsDimmed: false },
  {
    title: 'En discussion',
    statuses: ['contacted', 'waiting'],
    emptyMessage: null,
    caption: null,
    areCardsDimmed: false,
  },
  {
    title: 'Réservé',
    statuses: ['reserved'],
    emptyMessage: 'Rien pour l’instant. Quand tu réserves ton chiot, il arrive ici avec sa date de départ.',
    caption: null,
    areCardsDimmed: false,
  },
  {
    title: 'Écartées',
    statuses: ['dismissed'],
    emptyMessage: null,
    caption: 'Plus dans Portées ni sur la carte',
    areCardsDimmed: true,
  },
]
