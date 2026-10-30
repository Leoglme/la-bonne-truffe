import type { NotificationKind, NotificationLitter, SentNotification } from '~/types/api'
import type { DevicePosition } from '~/types/Location'
import type { NotificationDayDefinition, NotificationDayKey, NotificationDaySection } from '~/types/Notification'
import { NOTIFICATION_DAY_SECTIONS } from '~/constants/notificationKinds'
import { FollowUpPresentation } from '~/utils/followUpPresentation'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

const LITTER_EVENT_KINDS: NotificationKind[] = ['born', 'new_preferred', 'upgraded']

/** How the bell words a notification: its day, its time, and the facts of its litter. */
export class NotificationPresentation {
  /**
   * Group the notifications by day, newest first inside each day.
   *
   * @param notifications - The history, newest first.
   * @param now - Current time.
   * @returns « Aujourd’hui », « Hier » and « Plus tôt », without the empty ones.
   */
  static groupByDay(notifications: SentNotification[], now: Date): NotificationDaySection[] {
    return NOTIFICATION_DAY_SECTIONS.map((day: NotificationDayDefinition): NotificationDaySection => ({
      ...day,
      notifications: notifications.filter(
        (notification: SentNotification): boolean => this.resolveDayKey(notification.sent_at, now) === day.key,
      ),
    })).filter((section: NotificationDaySection): boolean => section.notifications.length > 0)
  }

  /**
   * Write when a notification was sent, as short as its day allows.
   *
   * @param sentAt - Sending time, from the API.
   * @param now - Current time.
   * @returns « il y a 20 min » today, « hier », or « 27 oct. ».
   */
  static buildTimeLabel(sentAt: string, now: Date): string {
    const sentMoment: Date = FrenchDate.parseApiDate(sentAt)
    const dayKey: NotificationDayKey = this.resolveDayKey(sentAt, now)
    if (dayKey === 'today') {
      return FrenchDate.formatTimeSince(sentMoment, now)
    }
    return dayKey === 'yesterday' ? 'hier' : FrenchDate.formatDayAndShortMonth(sentMoment)
  }

  /**
   * Whether a notification tells about one litter whose facts the card can show.
   *
   * @param kind - Kind of the notification.
   * @returns True for a birth, a preferred litter or an upgrade.
   */
  static isLitterEvent(kind: NotificationKind): boolean {
    return LITTER_EVENT_KINDS.includes(kind)
  }

  /**
   * Write the fact of a litter event before its sexes: when it was born, or when it is due.
   *
   * @param litter - The litter.
   * @returns « Née le 27 oct. », « À naître vers le 7 nov. », or null when nothing is known.
   */
  static buildLitterFact(litter: NotificationLitter): string | null {
    if (litter.kind === 'litter_expected') {
      const expectedBirthPhrase: string = FollowUpPresentation.buildExpectedBirthPhrase(litter)
      return expectedBirthPhrase.charAt(0).toUpperCase() + expectedBirthPhrase.slice(1)
    }
    if (litter.birth_date === null) {
      return null
    }
    return `Née le ${FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(litter.birth_date))}`
  }

  /**
   * Write what comes after the sexes of a born litter: when the puppies can leave.
   *
   * @param litter - The litter.
   * @returns « dispo vers le 22 déc. », or null before the birth or while unknown.
   */
  static buildAvailabilityFact(litter: NotificationLitter): string | null {
    if (litter.kind === 'litter_expected' || litter.available_from === null) {
      return null
    }
    return `dispo vers le ${FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(litter.available_from))}`
  }

  /**
   * Build the last line of a litter: where it is, how far, its colour.
   *
   * @param litter - The litter.
   * @param position - Position of the device, null while unknown.
   * @returns « Redon · à 32 km · gold », « Dinan · couleur à confirmer ».
   */
  static buildPlaceAndColorLine(litter: NotificationLitter, position: DevicePosition | null): string {
    const parts: (string | null)[] = [
      LitterPresentation.buildPlace(litter),
      LitterPresentation.buildDistanceLabel(litter, position),
      LitterPresentation.buildColorLabel(litter.colors, false).toLowerCase(),
    ]
    return parts.filter((part: string | null): part is string => part !== null).join(' · ')
  }

  /**
   * Write the puppies a followed litter still offers, for a line of the digest.
   *
   * @param litter - The litter.
   * @returns « plus qu’un chiot disponible », « plus que 2 chiots disponibles », « plus aucun chiot disponible ».
   */
  static buildPuppiesLeftPhrase(litter: NotificationLitter): string {
    if (litter.puppies_available === null) {
      return 'moins de chiots disponibles'
    }
    if (litter.puppies_available === 0) {
      return 'plus aucun chiot disponible'
    }
    if (litter.puppies_available === 1) {
      return 'plus qu’un chiot disponible'
    }
    return `plus que ${litter.puppies_available} chiots disponibles`
  }

  /**
   * Tell the day a notification belongs to.
   *
   * @param sentAt - Sending time, from the API.
   * @param now - Current time.
   * @returns Today, yesterday, or earlier.
   */
  private static resolveDayKey(sentAt: string, now: Date): NotificationDayKey {
    const sentMoment: Date = FrenchDate.parseApiDate(sentAt)
    const sentDay: Date = new Date(sentMoment.getFullYear(), sentMoment.getMonth(), sentMoment.getDate())
    const daysAgo: number = FrenchDate.countDaysAgo(sentDay, now)
    if (daysAgo <= 0) {
      return 'today'
    }
    return daysAgo === 1 ? 'yesterday' : 'earlier'
  }
}
