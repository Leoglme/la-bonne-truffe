import type { ColorPreferenceLevel, FollowUpStatus, LofPreference, SexPreference } from '~/types/api'
import { COLOR_LEVELS, LOF_PREFERENCES, NEVER_HIDE_PUPPIES_CHOICE, SEX_PREFERENCES } from '~/constants/criteriaOptions'
import { FOLLOW_UP_STATUSES } from '~/constants/followUpOptions'

/** Narrow the string that choice buttons emit back to the typed values of the API, and the values back to a choice. */
export class ChoiceValues {
  /**
   * Whether a value is a colour level.
   *
   * @param value - Emitted value.
   * @returns True for « preferred », « acceptable » or « ignored ».
   */
  static isColorLevel(value: string): value is ColorPreferenceLevel {
    return COLOR_LEVELS.some((level: ColorPreferenceLevel): boolean => level === value)
  }

  /**
   * Whether a value is a LOF preference.
   *
   * @param value - Emitted value.
   * @returns True for « required », « preferred » or « any ».
   */
  static isLofPreference(value: string): value is LofPreference {
    return LOF_PREFERENCES.some((preference: LofPreference): boolean => preference === value)
  }

  /**
   * Whether a value is a sex preference.
   *
   * @param value - Emitted value.
   * @returns True for « male », « female » or « any ».
   */
  static isSexPreference(value: string): value is SexPreference {
    return SEX_PREFERENCES.some((preference: SexPreference): boolean => preference === value)
  }

  /**
   * Whether a value is a follow-up status.
   *
   * @param value - Emitted value.
   * @returns True for a known status.
   */
  static isFollowUpStatus(value: string): value is FollowUpStatus {
    return FOLLOW_UP_STATUSES.some((status: FollowUpStatus): boolean => status === value)
  }

  /**
   * Days behind a « Chiots déjà partis » choice.
   *
   * @param choice - Emitted value: the days, or « never ».
   * @returns The days; null for « never » or a value that is not a whole number.
   */
  static maxPuppyAgeDaysOf(choice: string): number | null {
    const days: number = Number(choice)
    return choice === NEVER_HIDE_PUPPIES_CHOICE || !Number.isInteger(days) ? null : days
  }

  /**
   * The choice that shows the age limit of a profile.
   *
   * @param days - Days of the profile, null for no limit.
   * @returns The days as a string, « never » for null.
   */
  static maxPuppyAgeChoiceOf(days: number | null): string {
    return days === null ? NEVER_HIDE_PUPPIES_CHOICE : String(days)
  }
}
