import type { BreederDetail } from '~/types/api'

export type BreederAddLinkDialogProps = {
  open: boolean
  breeder: BreederDetail
}

export type BreederAddLinkDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
