export type LitterSortDrawerProps = {
  open: boolean
}

export type LitterSortDrawerEmits = {
  (event: 'update:open', isOpen: boolean): void
}
