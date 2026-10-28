export type UiPasswordInputAutocomplete = 'current-password' | 'new-password'

export type UiPasswordInputProps = {
  modelValue: string
  autocomplete: UiPasswordInputAutocomplete
}

export type UiPasswordInputEmits = {
  (event: 'update:modelValue', value: string): void
}
