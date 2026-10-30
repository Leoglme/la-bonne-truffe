import type { CoatColor } from '~/types/api'
import type { CockerCoat } from '~/types/CockerCoat'

export type CriteriaColorRow = {
  color: CoatColor
  coat: CockerCoat
}

export type CriteriaHourOption = {
  label: string
  value: number
}
