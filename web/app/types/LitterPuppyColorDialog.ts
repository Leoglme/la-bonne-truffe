import type { LitterDetail } from '~/types/api'
import type { LitterPuppyLine } from '~/types/Litter'

export type LitterPuppyColorDialogProps = {
  open: boolean
  litter: LitterDetail
  puppyLine: LitterPuppyLine | null
}

export type LitterPuppyColorDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
