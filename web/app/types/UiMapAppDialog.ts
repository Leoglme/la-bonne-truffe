import type { MapDestination } from '~/types/Location'

export type UiMapAppDialogProps = {
  open: boolean
  destination: MapDestination
}

export type UiMapAppDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
