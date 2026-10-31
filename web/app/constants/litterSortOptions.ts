import type { LitterSortKey, LitterSortOption } from '~/types/Litter'

export const DEFAULT_LITTER_SORT_OPTION: LitterSortOption = {
  key: 'score',
  label: 'Meilleur score',
  description: 'Ce qui te correspond le plus, en premier',
}

export const LITTER_SORT_OPTIONS: LitterSortOption[] = [
  DEFAULT_LITTER_SORT_OPTION,
  { key: 'distance', label: 'Les plus proches', description: 'Depuis chez toi, à vol d’oiseau' },
  { key: 'price', label: 'Les moins chères', description: 'Prix inconnu en dernier' },
  { key: 'departure_soonest', label: 'Départ le plus tôt', description: 'Le chiot que tu pourrais ramener en premier' },
  { key: 'departure_latest', label: 'Départ le plus tard', description: 'Si tu n’es pas pressé' },
]

export const LITTER_SORT_KEYS: LitterSortKey[] = LITTER_SORT_OPTIONS.map(
  (option: LitterSortOption): LitterSortKey => option.key,
)

export const DEFAULT_LITTER_SORT_KEY: LitterSortKey = DEFAULT_LITTER_SORT_OPTION.key
