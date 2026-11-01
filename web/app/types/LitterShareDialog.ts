import type { LitterDetail } from '~/types/api'

export type LitterShareDialogProps = {
  open: boolean
  litter: LitterDetail
}

export type LitterShareDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
