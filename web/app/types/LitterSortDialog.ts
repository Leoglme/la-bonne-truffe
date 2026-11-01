export type LitterSortDialogProps = {
  open: boolean
}

export type LitterSortDialogEmits = {
  (event: 'update:open', isOpen: boolean): void
}
