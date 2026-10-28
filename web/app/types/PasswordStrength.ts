export type PasswordStrengthLevel = 'empty' | 'too-weak' | 'fair' | 'strong' | 'very-strong'

export type PasswordStrengthDisplay = {
  filledSegmentCount: number
  label: string
  segmentClass: string
  labelClass: string
}
