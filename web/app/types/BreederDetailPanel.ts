import type { BreederDetail } from '~/types/api'

export type BreederDetailPanelProps = {
  breeder: BreederDetail
}

export type BreederDetailPanelEmits = {
  (event: 'close'): void
}
