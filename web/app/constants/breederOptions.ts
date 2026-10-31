import type { BreederFollowStatus, BreederFollowUpdate, CoatColor } from '~/types/api'
import type {
  BreederChipTone,
  BreederFilterOption,
  BreederFollowStatusOption,
  BreederLitterStatusTone,
  BreederNotificationSetting,
  BreederSortOption,
} from '~/types/Breeder'

export const BREEDER_FILTER_OPTIONS: BreederFilterOption[] = [
  { key: 'all', label: 'Tous' },
  { key: 'followed', label: 'Suivis' },
  { key: 'gold', label: 'Gold' },
  { key: 'club', label: 'Spaniel Club' },
  { key: 'active_litter', label: 'Une portée en cours' },
]

export const BREEDER_SORT_OPTIONS: BreederSortOption[] = [
  { key: 'promising', label: 'Les plus prometteurs d’abord' },
  { key: 'name', label: 'Par nom' },
]

/** Where the exchange with a breeder stands, as the card and the drawer word it. */
export const BREEDER_FOLLOW_STATUS_LABELS: Record<BreederFollowStatus, string> = {
  to_contact: 'À contacter',
  contacted: 'Contacté',
  waiting: 'Sur liste d’attente',
  deposit: 'Acompte versé',
}

const BREEDER_FOLLOW_STATUSES: BreederFollowStatus[] = ['to_contact', 'contacted', 'waiting', 'deposit']

export const BREEDER_FOLLOW_STATUS_OPTIONS: BreederFollowStatusOption[] = BREEDER_FOLLOW_STATUSES.map(
  (value: BreederFollowStatus): BreederFollowStatusOption => ({ value, label: BREEDER_FOLLOW_STATUS_LABELS[value] }),
)

/** The alerts a follow can send, in the order of the drawer. */
export const BREEDER_NOTIFICATION_SETTINGS: BreederNotificationSetting[] = [
  {
    key: 'notify_new_mating',
    label: 'Nouvelle saillie déclarée',
    helper: 'Dès qu’elle paraît à la Centrale Canine, quatre mois avant le départ des chiots',
  },
  {
    key: 'notify_birth',
    label: 'Naissance d’une portée',
    helper: 'Avec les mâles et les femelles, pour appeler dans l’heure',
  },
  {
    key: 'notify_new_photos',
    label: 'Nouvelles photos ou nouvelle annonce',
    helper: 'Sur son site Chiens de France, Chiots de France ou Whoof, dans le récap du soir',
  },
  {
    key: 'notify_ignored_colors',
    label: 'Même pour une couleur que j’ignore',
    helper: 'Sinon, seulement les couleurs de tes critères',
  },
]

/** The follow a heart starts with. */
export const DEFAULT_BREEDER_FOLLOW: BreederFollowUpdate = {
  status: 'to_contact',
  notify_new_mating: true,
  notify_birth: true,
  notify_new_photos: true,
  notify_ignored_colors: false,
  next_reminder_at: null,
  last_contact_at: null,
}

export const BREEDER_CHIP_CLASSES: Record<BreederChipTone, string> = {
  neutral: 'bg-chip text-ink-secondary',
  gold: 'bg-gold-pastel text-gold-ink',
  coral: 'bg-coral-pastel text-coral-text',
  green: 'bg-lof-pastel text-lof-ink',
  lilac: 'bg-lilac-pastel text-ink-secondary',
}

export const BREEDER_LITTER_STATUS_LINE_CLASSES: Record<BreederLitterStatusTone, string> = {
  hot: 'font-extrabold text-coral-text',
  normal: 'font-bold text-ink-secondary',
  inactive: 'font-bold text-ink-muted',
}

/** The colour of each coat in the bar of « Ses couleurs ». */
export const COAT_COLOR_SWATCHES: Record<CoatColor, string> = {
  gold: '#E9B363',
  noir: '#2F2724',
  noir_et_feu: '#3A2F2A',
  marron: '#7B5033',
  marron_et_feu: '#8B5A3C',
  bleu_rouan: '#8B8F99',
  orange_rouan: '#E0A070',
  marron_rouan: '#A07860',
  tricolore: '#C8A070',
  particolore: '#D8C8B0',
  zibeline: '#A0703C',
  inconnue: '#D9CFC2',
}

/** How many litters the breeder page shows before « les autres portées ». */
export const BREEDER_LITTERS_SHOWN_COUNT: number = 3

export const BREEDER_RECENT_SEARCHES_STORAGE_KEY: string = 'lbt-breeder-searches'
export const BREEDER_RECENT_SEARCHES_COUNT: number = 5
export const BREEDER_SEARCH_DEBOUNCE_MS: number = 250
export const BREEDER_SIMILAR_NAMES_COUNT: number = 2
