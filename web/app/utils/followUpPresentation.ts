import type { FollowUpCard, FollowUpStatus } from '~/types/api'
import { LitterPresentation } from '~/utils/litterPresentation'

/** A section of the follow-up screen. */
export type FollowUpSection = {
  title: string
  statuses: readonly FollowUpStatus[]
  emptyMessage: string | null
}

/** The reminder chip of a follow-up card. */
export type FollowUpReminderChip = {
  label: string
  isUrgent: boolean
}

/** Sections of design/mockup/Suivi.dc.html; dismissed litters are not shown. */
export const FOLLOW_UP_SECTIONS: readonly FollowUpSection[] = [
  { title: 'À appeler', statuses: ['new', 'to_contact'], emptyMessage: null },
  { title: 'En discussion', statuses: ['contacted', 'waiting'], emptyMessage: null },
  {
    title: 'Réservé',
    statuses: ['reserved'],
    emptyMessage: 'Rien pour l’instant. Quand tu réserves ton chiot, il arrive ici avec sa date de départ.',
  },
]

const WEEKDAYS: readonly string[] = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']

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
    return new Date(`${card.next_reminder_at}Z`).getTime() < endOfToday.getTime()
  }

  /**
   * The reminder chip of a card.
   *
   * @param card - The follow-up.
   * @param now - Current time.
   * @returns « Aujourd’hui », « Avant vendredi », « Relancer le 30 oct. », « Rappel à la naissance », or null.
   */
  static reminderChip(card: FollowUpCard, now: Date): FollowUpReminderChip | null {
    if (card.next_reminder_at === null) {
      return card.litter.kind === 'litter_expected' ? { label: 'Rappel à la naissance', isUrgent: false } : null
    }
    if (this.isDue(card, now)) {
      return { label: 'Aujourd’hui', isUrgent: true }
    }
    const reminder: Date = new Date(`${card.next_reminder_at}Z`)
    const isoDay: string = `${reminder.getFullYear()}-${String(reminder.getMonth() + 1).padStart(2, '0')}-${String(reminder.getDate()).padStart(2, '0')}`
    if (card.status === 'contacted' || card.status === 'waiting') {
      return { label: `Relancer le ${LitterPresentation.shortDay(isoDay)}`, isUrgent: false }
    }
    const daysAhead: number = Math.ceil((reminder.getTime() - now.getTime()) / 86_400_000)
    return daysAhead <= 6
      ? { label: `Avant ${WEEKDAYS[reminder.getDay()] ?? ''}`, isUrgent: false }
      : { label: `Avant le ${LitterPresentation.shortDay(isoDay)}`, isUrgent: false }
  }

  /**
   * The line under the name: place, sexes or expected birth, colour.
   *
   * @param card - The follow-up.
   * @returns « Redon · 2 ♂ · 3 ♀ · gold ».
   */
  static summaryLine(card: FollowUpCard): string {
    const litter: FollowUpCard['litter'] = card.litter
    const middle: string =
      litter.kind === 'litter_expected'
        ? litter.expected_birth_date
          ? `à naître vers le ${LitterPresentation.shortDay(litter.expected_birth_date)}`
          : 'à naître'
        : LitterPresentation.sexLine(litter)
    const color: string = LitterPresentation.colorLabel(litter.colors, true).toLowerCase()
    return [litter.town ?? litter.place ?? 'Lieu à confirmer', middle, color].join(' · ')
  }
}
