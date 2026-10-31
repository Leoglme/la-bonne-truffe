import type { BreederCard } from '~/types/api'

export type BreederGridCardProps = {
  breeder: BreederCard
  isSelected: boolean
}

export type BreederGridCardEmits = {
  (event: 'activate', clickEvent: MouseEvent): void
}
