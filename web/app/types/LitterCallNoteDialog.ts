import type { LitterDetail } from '~/types/api'

export type LitterCallNoteDialogProps = {
  open: boolean
  litter: LitterDetail
}

export type LitterCallNoteDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
