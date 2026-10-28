import type { LitterCard, LitterDetail, LitterSourceListing } from '~/types/api'
import type { LitterKeyFact, LitterPrimaryAction } from '~/types/Litter'
import { LISTING_KIND_LABELS, LISTING_SOURCE_LABELS, LISTING_SOURCE_LINK_LABELS } from '~/constants/litterLabels'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

const UNKNOWN_FACT_LABEL: string = 'À confirmer'

/** How the detail screen and the desktop panel word a litter. */
export class LitterDetailPresentation {
  /**
   * Build the badge over the photo.
   *
   * @param litter - The litter.
   * @param now - Current time.
   * @returns « NÉE CETTE NUIT », « À NAÎTRE », or null.
   */
  static buildPhotoBadge(litter: LitterCard, now: Date): string | null {
    if (litter.kind === 'litter_expected') {
      return 'À NAÎTRE'
    }
    if (LitterPresentation.isBornLastNight(litter, now)) {
      return 'NÉE CETTE NUIT'
    }
    return null
  }

  /**
   * Build the place line under the name: the town and its department.
   *
   * @param litter - The litter.
   * @returns « Redon, Ille-et-Vilaine », or the department alone.
   */
  static buildTownAndDepartment(litter: LitterCard): string {
    const parts: string[] = [litter.town, litter.department_name].filter(
      (part: string | null): part is string => part !== null,
    )
    if (parts.length === 0) {
      return LitterPresentation.buildPlace(litter)
    }
    return parts.join(', ')
  }

  /**
   * Build the three key facts.
   *
   * @param litter - The litter.
   * @returns Birth (or expected birth), puppies, departure.
   */
  static buildKeyFacts(litter: LitterCard): LitterKeyFact[] {
    const puppies: string = LitterPresentation.buildSexLine(litter)
    return [
      this.buildBirthFact(litter),
      { label: 'Chiots', value: puppies, compactValue: puppies },
      this.buildApproximateDayFact('Départ', litter.available_from),
    ]
  }

  /**
   * Build the « Vu sur » line of a listing.
   *
   * @param listing - The listing.
   * @returns « Centrale Canine · déclaration de naissance ».
   */
  static buildSourceLine(listing: LitterSourceListing): string {
    return `${LISTING_SOURCE_LABELS[listing.source]} · ${LISTING_KIND_LABELS[listing.kind]}`
  }

  /**
   * Pick where the primary button leads: the breeder's phone when known, else the litter on its source.
   *
   * @param litter - The litter.
   * @returns The link and its label, or null when nothing is known.
   */
  static resolvePrimaryAction(litter: LitterDetail): LitterPrimaryAction | null {
    const phone: string | null = litter.breeder?.phone_e164 ?? null
    if (phone !== null) {
      return { href: `tel:${phone}`, label: 'Appeler l’éleveur', isCall: true }
    }
    const sourceListing: LitterSourceListing | undefined = litter.listings.find(
      (listing: LitterSourceListing): boolean => listing.external_url !== null,
    )
    if (sourceListing?.external_url) {
      return {
        href: sourceListing.external_url,
        label: LISTING_SOURCE_LINK_LABELS[sourceListing.source],
        isCall: false,
      }
    }
    return null
  }

  /**
   * Build the birth fact: the expected day for a litter to come, the birth day otherwise.
   *
   * @param litter - The litter.
   * @returns « Naissance vers le 7 nov. » or « Née le 27 octobre ».
   */
  private static buildBirthFact(litter: LitterCard): LitterKeyFact {
    if (litter.kind === 'litter_expected') {
      return this.buildApproximateDayFact('Naissance', litter.expected_birth_date)
    }
    if (litter.birth_date === null) {
      return { label: 'Née le', value: UNKNOWN_FACT_LABEL, compactValue: UNKNOWN_FACT_LABEL }
    }
    const birthDay: Date = FrenchDate.parseDay(litter.birth_date)
    return {
      label: 'Née le',
      value: FrenchDate.formatDayAndLongMonth(birthDay),
      compactValue: FrenchDate.formatDayAndShortMonth(birthDay),
    }
  }

  /**
   * Build a fact that holds an approximate day.
   *
   * @param label - « Naissance » or « Départ ».
   * @param isoDay - The day from the API, null while unknown.
   * @returns « vers le 22 déc. » on the iPad, « 22 déc. » on the phone and the panel.
   */
  private static buildApproximateDayFact(label: string, isoDay: string | null): LitterKeyFact {
    if (isoDay === null) {
      return { label, value: UNKNOWN_FACT_LABEL, compactValue: UNKNOWN_FACT_LABEL }
    }
    const shortDay: string = FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(isoDay))
    return { label, value: `vers le ${shortDay}`, compactValue: shortDay }
  }
}
