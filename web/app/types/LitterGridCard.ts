import type { LitterCard } from '~/types/api'

export type LitterGridCardProps = {
  litter: LitterCard
  isNew: boolean
  isSelected: boolean
}

export type LitterGridCardEmits = {
  (event: 'activate', clickEvent: MouseEvent): void
}
