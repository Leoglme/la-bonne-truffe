const FRENCH_LOCALE: string = 'fr-FR'
const MILLISECONDS_PER_MINUTE: number = 60_000
const MILLISECONDS_PER_DAY: number = 86_400_000
const TIME_ZONE_SUFFIX: RegExp = /(Z|[+-]\d{2}:?\d{2})$/i

const DAY_AND_LONG_MONTH_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat(FRENCH_LOCALE, {
  day: 'numeric',
  month: 'long',
})
const DAY_AND_SHORT_MONTH_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat(FRENCH_LOCALE, {
  day: 'numeric',
  month: 'short',
})
const WEEKDAY_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat(FRENCH_LOCALE, { weekday: 'long' })
const DAY_AND_TIME_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat(FRENCH_LOCALE, {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
})

/** API dates read as the instant or the day they stand for, then written the French way. */
export class FrenchDate {
  /**
   * Read an API date-time, sent in UTC without a zone, as the instant it stands for.
   *
   * @param isoDateTime - Date-time from the API, such as `2026-10-28T08:00:00`.
   * @returns The date at that instant.
   */
  static parseApiDate(isoDateTime: string): Date {
    return new Date(TIME_ZONE_SUFFIX.test(isoDateTime) ? isoDateTime : `${isoDateTime}Z`)
  }

  /**
   * Read a day written `2026-10-27`, by the API or a date input, as that calendar day at local midnight.
   *
   * @param isoDay - The day.
   * @returns The date at local midnight.
   */
  static parseDay(isoDay: string): Date {
    return new Date(`${isoDay}T00:00:00`)
  }

  /**
   * Write a day with its month in full.
   *
   * @param day - The day.
   * @returns « 27 octobre ».
   */
  static formatDayAndLongMonth(day: Date): string {
    return DAY_AND_LONG_MONTH_FORMAT.format(day)
  }

  /**
   * Write a day with its month abbreviated.
   *
   * @param day - The day.
   * @returns « 22 déc. ».
   */
  static formatDayAndShortMonth(day: Date): string {
    return DAY_AND_SHORT_MONTH_FORMAT.format(day)
  }

  /**
   * Write the weekday of a date.
   *
   * @param day - The day.
   * @returns « vendredi ».
   */
  static formatWeekday(day: Date): string {
    return WEEKDAY_FORMAT.format(day)
  }

  /**
   * Write a moment with its weekday, its day and its time.
   *
   * @param moment - The moment.
   * @returns « vendredi 30 octobre à 09:00 ».
   */
  static formatDayAndTime(moment: Date): string {
    return DAY_AND_TIME_FORMAT.format(moment)
  }

  /**
   * Write a date as the local day a date input holds.
   *
   * @param day - The day.
   * @returns « 2026-10-28 ».
   */
  static formatInputDay(day: Date): string {
    const month: string = String(day.getMonth() + 1).padStart(2, '0')
    const dayOfMonth: string = String(day.getDate()).padStart(2, '0')
    return `${day.getFullYear()}-${month}-${dayOfMonth}`
  }

  /**
   * Write a moment as the local day and time a date-time input holds.
   *
   * @param moment - The moment.
   * @returns « 2026-10-30T09:00 ».
   */
  static formatInputDayAndTime(moment: Date): string {
    const hours: string = String(moment.getHours()).padStart(2, '0')
    const minutes: string = String(moment.getMinutes()).padStart(2, '0')
    return `${this.formatInputDay(moment)}T${hours}:${minutes}`
  }

  /**
   * Write how long ago a moment was.
   *
   * @param moment - The past moment.
   * @param now - Current time.
   * @returns « à l’instant », « il y a 12 min », « il y a 3 h » or « il y a 2 j ».
   */
  static formatTimeSince(moment: Date, now: Date): string {
    const elapsedMinutes: number = Math.max(0, Math.floor((now.getTime() - moment.getTime()) / MILLISECONDS_PER_MINUTE))
    if (elapsedMinutes < 1) {
      return 'à l’instant'
    }
    if (elapsedMinutes < 60) {
      return `il y a ${elapsedMinutes} min`
    }
    const elapsedHours: number = Math.floor(elapsedMinutes / 60)
    if (elapsedHours < 24) {
      return `il y a ${elapsedHours} h`
    }
    return `il y a ${Math.floor(elapsedHours / 24)} j`
  }

  /**
   * Count the calendar days between a day and today.
   *
   * @param day - The day, at local midnight.
   * @param now - Current time.
   * @returns 0 for today, 1 for yesterday, a negative count for a day to come.
   */
  static countDaysAgo(day: Date, now: Date): number {
    const startOfToday: Date = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    return Math.round((startOfToday.getTime() - day.getTime()) / MILLISECONDS_PER_DAY)
  }

  /**
   * Count the days left until a moment, a started day counting as a whole one.
   *
   * @param moment - The moment to come.
   * @param now - Current time.
   * @returns The number of days, rounded up.
   */
  static countDaysUntil(moment: Date, now: Date): number {
    return Math.ceil((moment.getTime() - now.getTime()) / MILLISECONDS_PER_DAY)
  }
}
