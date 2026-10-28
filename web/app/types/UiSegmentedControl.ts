/** One choice of a segmented control. */
export type UiSegmentedControlOption = {
  value: string
  label: string
}

export type UiSegmentedControlProps = {
  modelValue: string
  options: UiSegmentedControlOption[]
  label: string
}

export type UiSegmentedControlEmits = {
  (event: 'update:modelValue', value: string): void
}
