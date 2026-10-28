import type { PasswordStrengthLevel } from '~/types/PasswordStrength'
import { PASSWORD_LONG_LENGTH, PASSWORD_MIN_LENGTH } from '~/constants/passwordRules'

/** The rule a new password follows, and how far beyond it a password goes. */
export class PasswordRules {
  /**
   * Whether a password follows the rule the screens announce.
   *
   * @param password - Password typed on the signup or reset screen.
   * @returns True with 8 characters minimum, a digit among them.
   */
  static isStrongEnough(password: string): boolean {
    return password.length >= PASSWORD_MIN_LENGTH && /\d/.test(password)
  }

  /**
   * Measure how strong a new password is: below the rule, just the rule, then one level for length and one for variety.
   *
   * @param password - Password typed on the signup or reset screen.
   * @returns The level the strength meter shows.
   */
  static measureStrengthLevel(password: string): PasswordStrengthLevel {
    if (!password) {
      return 'empty'
    }
    if (!this.isStrongEnough(password)) {
      return 'too-weak'
    }
    const isLong: boolean = password.length >= PASSWORD_LONG_LENGTH
    const isVaried: boolean = (/[a-z]/.test(password) && /[A-Z]/.test(password)) || /[^A-Za-z0-9]/.test(password)
    if (isLong && isVaried) {
      return 'very-strong'
    }
    if (isLong || isVaried) {
      return 'strong'
    }
    return 'fair'
  }
}
