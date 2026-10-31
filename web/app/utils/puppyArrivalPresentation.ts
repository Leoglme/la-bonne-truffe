import type { LitterDetail } from '~/types/api'
import { PUPPY_ARRIVAL_CHECKLIST_KEYS } from '~/constants/puppyArrivalChecklist'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

/** How the « chiot trouvé » screen reads: the countdown, the sentence about the puppy, the preparations done. */
export class PuppyArrivalPresentation {
  /**
   * Count the calendar days left before the arrival.
   *
   * @param arrivalOn - Arrival day, from the API.
   * @param now - Current time.
   * @returns 0 on the day, a negative count once it is past.
   */
  static countDaysLeft(arrivalOn: string, now: Date): number {
    return -FrenchDate.countDaysAgo(FrenchDate.parseDay(arrivalOn), now)
  }

  /**
   * Build the badge over the photo.
   *
   * @param daysLeft - Days left before the arrival.
   * @returns « J-23 », or null from the day of the arrival.
   */
  static buildCountdownBadge(daysLeft: number): string | null {
    return daysLeft > 0 ? `J-${daysLeft}` : null
  }

  /**
   * Say on which day the puppy arrives, or arrived.
   *
   * @param arrivalOn - Arrival day, from the API.
   * @param daysLeft - Days left before the arrival.
   * @returns « Il arrive le 22 décembre », « Il arrive aujourd’hui » or « Il est arrivé le 22 décembre ».
   */
  static buildArrivalDayLabel(arrivalOn: string, daysLeft: number): string {
    const arrivalDay: string = FrenchDate.formatDayAndLongMonth(FrenchDate.parseDay(arrivalOn))
    if (daysLeft === 0) {
      return 'Il arrive aujourd’hui'
    }
    return daysLeft > 0 ? `Il arrive le ${arrivalDay}` : `Il est arrivé le ${arrivalDay}`
  }

  /**
   * Build the title of the screen.
   *
   * @param daysLeft - Days left before the arrival.
   * @returns « Plus que 23 jours », « Plus qu’un jour », « C’est le grand jour » or « Bienvenue à la maison ».
   */
  static buildTitle(daysLeft: number): string {
    if (daysLeft > 1) {
      return `Plus que ${daysLeft} jours`
    }
    if (daysLeft === 1) {
      return 'Plus qu’un jour'
    }
    return daysLeft === 0 ? 'C’est le grand jour' : 'Bienvenue à la maison'
  }

  /**
   * Say whose puppy it is and where it comes from.
   *
   * @param litter - Litter of the puppy, null once it left the database.
   * @returns « Ton chiot gold Des Bords de Vilaine, chez Marie Le Gall à Redon. », the unknown parts left out.
   */
  static buildSentence(litter: LitterDetail | null): string {
    if (litter === null) {
      return 'Ton chiot arrive bientôt.'
    }
    const colorPart: string = LitterPresentation.hasKnownColors(litter.colors)
      ? ` ${LitterPresentation.buildColorPhrase(litter.colors)}`
      : ''
    const breederName: string | null = litter.breeder?.display_name ?? null
    const breederPart: string = breederName && breederName !== litter.name ? `, chez ${breederName}` : ''
    const townPart: string = litter.town ? ` à ${litter.town}` : ''
    return `Ton chiot${colorPart} ${litter.name}${breederPart}${townPart}.`
  }

  /**
   * Remind that the alerts wait.
   *
   * @param pausedSince - When the search was paused, from the API.
   * @returns « Les alertes sont en pause depuis le 29 oct. ».
   */
  static buildPausedLine(pausedSince: string): string {
    return `Les alertes sont en pause depuis le ${FrenchDate.formatDayAndShortMonth(FrenchDate.parseApiDate(pausedSince))}`
  }

  /**
   * Count the preparations done among the ones of the list.
   *
   * @param donePreparationKeys - Keys ticked, from the API.
   * @returns How many of the list are ticked.
   */
  static countDonePreparations(donePreparationKeys: string[]): number {
    return PUPPY_ARRIVAL_CHECKLIST_KEYS.filter((key: string): boolean => donePreparationKeys.includes(key)).length
  }

  /**
   * Pick the arrival day the « C’est lui ? » card offers.
   *
   * @param litter - The litter reserved.
   * @param now - Current time.
   * @returns The departure day of the litter when it is still to come, else today, as a date input holds it.
   */
  static suggestArrivalDay(litter: LitterDetail, now: Date): string {
    const today: string = FrenchDate.formatInputDay(now)
    return litter.available_from !== null && litter.available_from > today ? litter.available_from : today
  }
}
