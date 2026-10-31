import type { LitterDetail } from '~/types/api'

export type LitterShareDrawerProps = {
  open: boolean
  litter: LitterDetail
}

export type LitterShareDrawerEmits = {
  (event: 'update:open', isOpen: boolean): void
}
