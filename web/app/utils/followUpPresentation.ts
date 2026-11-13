import type { FollowUpCard, LitterCard } from '~/types/api'
import type { FollowUpReminderChip } from '~/types/FollowUp'
import { FrenchDate } from '~/utils/frenchDate'

const WEEKDAY_REMINDER_DAY_LIMIT: number = 6
const EXPECTED_BIRTH_MARGIN_IN_DAYS: number = 3

/** How the follow-up screen words a followed litter. */
export class FollowUpPresentation {
  /**
   * Whether a reminder is due today or late.
   *
   * @param card - The follow-up.
   * @param now - Current time.
   * @returns True when the reminder time has come.
   */
  static isDue(card: FollowUpCard, now: Date): boolean {
    if (card.next_reminder_at === null) {
      return false
    }
    const endOfToday: Date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
    return FrenchDate.parseApiDate(card.next_reminder_at).getTime() < endOfToday.getTime()
  }

  /**
   * Build the reminder chip of a card.
   *
   * @param card - The follow-up.
   * @param now - Current time.
   * @returns « Aujourd’hui », « Avant vendredi », « Relancer le 30 oct. », « Rappel à la naissance », or null.
   */
  static buildReminderChip(card: FollowUpCard, now: Date): FollowUpReminderChip | null {
    if (card.next_reminder_at === null) {
      if (card.litter.kind === 'litter_expected') {
        return { label: 'Rappel à la naissance', isUrgent: false }
      }
      return null
    }
    if (this.isDue(card, now)) {
      return { label: 'Aujourd’hui', isUrgent: true }
    }
    const reminder: Date = FrenchDate.parseApiDate(card.next_reminder_at)
    if (card.status === 'contacted' || card.status === 'waiting') {
      return { label: `Relancer le ${FrenchDate.formatDayAndShortMonth(reminder)}`, isUrgent: false }
    }
    if (FrenchDate.countDaysUntil(reminder, now) <= WEEKDAY_REMINDER_DAY_LIMIT) {
      return { label: `Avant ${FrenchDate.formatWeekday(reminder)}`, isUrgent: false }
    }
    return { label: `Avant le ${FrenchDate.formatDayAndShortMonth(reminder)}`, isUrgent: false }
  }

  /**
   * Say when the breeder was last contacted.
   *
   * @param lastContactAt - Last contact, from the API, null before the first one.
   * @returns « Contacté le 24 oct. », or null.
   */
  static buildLastContactLabel(lastContactAt: string | null): string | null {
    if (lastContactAt === null) {
      return null
    }
    return `Contacté le ${FrenchDate.formatDayAndShortMonth(FrenchDate.parseApiDate(lastContactAt))}`
  }

  /**
   * Whether a litter to come should be born by now while no source has declared its birth.
   *
   * @param litter - The litter.
   * @param now - Current time.
   * @returns True once its expected birth is more than a few days old.
   */
  static isBirthOverdue(litter: LitterCard, now: Date): boolean {
    if (litter.kind !== 'litter_expected' || litter.expected_birth_date === null) {
      return false
    }
    const expectedBirthDay: Date = FrenchDate.parseDay(litter.expected_birth_date)
    return FrenchDate.countDaysAgo(expectedBirthDay, now) > EXPECTED_BIRTH_MARGIN_IN_DAYS
  }

  /**
   * Build the expected birth of a followed litter to come, for the line under its name.
   *
   * @param litter - The followed litter.
   * @param now - Current time.
   * @returns « à naître vers le 7 nov. », « à naître », or « attendue le 5 oct., naissance pas encore déclarée ».
   */
  static buildExpectedBirthPhrase(litter: LitterCard, now: Date = new Date()): string {
    if (litter.expected_birth_date === null) {
      return 'à naître'
    }
    const expectedBirthDay: string = FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(litter.expected_birth_date))
    if (this.isBirthOverdue(litter, now)) {
      return `attendue le ${expectedBirthDay}, naissance pas encore déclarée`
    }
    return `à naître vers le ${expectedBirthDay}`
  }
}
