import type { LitterSortKey } from '~/types/Litter'

export type LitterSortOptionsEmits = {
  (event: 'choose', sortKey: LitterSortKey): void
}
