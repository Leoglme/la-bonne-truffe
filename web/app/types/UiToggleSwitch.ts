export type UiToggleSwitchProps = {
  modelValue: boolean
  label: string
  isDisabled: boolean
}

export type UiToggleSwitchEmits = {
  (event: 'update:modelValue', value: boolean): void
}
