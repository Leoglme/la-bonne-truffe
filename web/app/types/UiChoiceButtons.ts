export type UiChoiceButtonsOption = {
  value: string
  label: string
}

export type UiChoiceButtonsProps = {
  modelValue: string
  options: UiChoiceButtonsOption[]
  label: string
  isDisabled: boolean
}

export type UiChoiceButtonsEmits = {
  (event: 'update:modelValue', value: string): void
}
