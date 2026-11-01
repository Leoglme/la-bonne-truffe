import type { DrawerProps } from '@nuxt/ui'

export type UiDialogProps = {
  open: boolean
  title: string
  description: string
  isWideWindow: boolean
  hasCreamBackground: boolean
  drawerUi: DrawerProps['ui']
}

export type UiDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
