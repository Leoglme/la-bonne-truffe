import type { LitterDetail } from '~/types/api'

export type LitterCallConfirmationProps = {
  litter: LitterDetail
  isInWideLayout: boolean
  isInWindow: boolean
}

export type LitterCallConfirmationEmits = {
  (event: 'closed'): void
}
