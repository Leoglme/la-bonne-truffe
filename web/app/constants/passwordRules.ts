import type { PasswordStrengthDisplay, PasswordStrengthLevel } from '~/types/PasswordStrength'

export const PASSWORD_MIN_LENGTH: number = 8

export const PASSWORD_LONG_LENGTH: number = 12

export const PASSWORD_STRENGTH_SEGMENT_COUNT: number = 4

export const PASSWORD_RULE_HINT: string = '8 caractères minimum, dont un chiffre'
export const PASSWORD_RULE_SHORT_HINT: string = '8 caractères, dont un chiffre'
export const PASSWORD_RULE_MESSAGE: string = 'Ton mot de passe doit faire 8 caractères minimum, dont un chiffre.'

export const PASSWORD_STRENGTH_DISPLAYS: Record<PasswordStrengthLevel, PasswordStrengthDisplay> = {
  empty: { filledSegmentCount: 0, label: '', segmentClass: '', labelClass: '' },
  'too-weak': { filledSegmentCount: 1, label: 'Trop faible', segmentClass: 'bg-coral', labelClass: 'text-coral-text' },
  fair: { filledSegmentCount: 2, label: 'Moyen', segmentClass: 'bg-gold-ink', labelClass: 'text-gold-ink' },
  strong: { filledSegmentCount: 3, label: 'Solide', segmentClass: 'bg-online', labelClass: 'text-lof-ink' },
  'very-strong': { filledSegmentCount: 4, label: 'Très solide', segmentClass: 'bg-online', labelClass: 'text-lof-ink' },
}
