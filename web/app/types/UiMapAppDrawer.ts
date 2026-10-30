import type { MapDestination } from '~/types/Location'

export type UiMapAppDrawerProps = {
  open: boolean
  destination: MapDestination
}

export type UiMapAppDrawerEmits = {
  (event: 'update:open', isOpen: boolean): void
}
