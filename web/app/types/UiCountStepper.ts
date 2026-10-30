export type UiCountStepperProps = {
  modelValue: number
  label: string
  maximum: number
}

export type UiCountStepperEmits = {
  (event: 'update:modelValue', value: number): void
}
