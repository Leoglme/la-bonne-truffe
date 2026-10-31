export type UiInlineConfirmationProps = {
  question: string
  consequence: string
  confirmLabel: string
  confirmAction: () => Promise<void>
}

export type UiInlineConfirmationEmits = {
  (event: 'cancelled'): void
}
