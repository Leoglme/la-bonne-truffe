import type { LitterDetail } from '~/types/api'

export type LitterDetailPanelProps = {
  litter: LitterDetail
}

export type LitterDetailPanelEmits = {
  (event: 'close'): void
}
