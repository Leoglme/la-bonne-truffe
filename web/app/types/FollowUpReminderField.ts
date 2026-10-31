export type FollowUpReminderFieldProps = {
  modelValue: string | null
  isDisabled: boolean
}

export type FollowUpReminderFieldEmits = {
  (event: 'update:modelValue', nextReminderAt: string | null): void
}
