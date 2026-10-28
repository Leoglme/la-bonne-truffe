import type { ColorPreferenceLevel, FollowUpStatus, LofPreference, SexPreference } from '~/types/api'
import { COLOR_LEVELS, LOF_PREFERENCES, SEX_PREFERENCES } from '~/constants/criteriaOptions'
import { FOLLOW_UP_STATUSES } from '~/constants/followUpOptions'

/** Narrow the string that choice buttons emit back to the typed values of the API. */
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
}
