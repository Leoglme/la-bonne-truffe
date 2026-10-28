import type { FollowUpCard, LitterCard } from '~/types/api'
import type { FollowUpReminderChip } from '~/types/FollowUp'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

const WEEKDAY_REMINDER_DAY_LIMIT: number = 6

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
   * Build the line under the name: place, sexes or expected birth, colour.
   *
   * @param card - The follow-up.
   * @returns « Redon · 2 ♂ · 3 ♀ · gold ».
   */
  static buildSummaryLine(card: FollowUpCard): string {
    const color: string = LitterPresentation.buildColorLabel(card.litter.colors, true).toLowerCase()
    return [LitterPresentation.buildPlace(card.litter), this.buildBirthOrSexes(card.litter), color].join(' · ')
  }

  /**
   * Build the middle of the summary line: the expected birth of a litter to come, the sexes otherwise.
   *
   * @param litter - The followed litter.
   * @returns « à naître vers le 7 nov. », « à naître » or « 2 ♂ · 3 ♀ ».
   */
  private static buildBirthOrSexes(litter: LitterCard): string {
    if (litter.kind !== 'litter_expected') {
      return LitterPresentation.buildSexLine(litter)
    }
    if (litter.expected_birth_date === null) {
      return 'à naître'
    }
    const expectedBirthDay: Date = FrenchDate.parseDay(litter.expected_birth_date)
    return `à naître vers le ${FrenchDate.formatDayAndShortMonth(expectedBirthDay)}`
  }
}
