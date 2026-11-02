import type { LitterFilterKey, LitterFilterOption } from '~/types/Litter'

export const LITTER_FILTER_OPTIONS: LitterFilterOption[] = [
  { key: 'all', label: 'Toutes' },
  { key: 'preferred', label: 'Préférées' },
  { key: 'expected', label: 'À naître' },
]

export const LITTER_FILTER_KEYS: LitterFilterKey[] = LITTER_FILTER_OPTIONS.map(
  (option: LitterFilterOption): LitterFilterKey => option.key,
)

export const DEFAULT_LITTER_FILTER_KEY: LitterFilterKey = 'all'
