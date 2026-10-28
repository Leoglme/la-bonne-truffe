import type { LitterCard, LitterDetail, LitterSourceListing, ListingSource } from '~/types/api'
import { LitterPresentation } from '~/utils/litterPresentation'

/** One of the three key facts of the detail screen (« Née le », « Chiots », « Départ »). */
export type LitterKeyFact = {
  label: string
  value: string
  compactValue: string
}

/** Where the primary button of the detail leads. */
export type LitterPrimaryAction = {
  href: string
  label: string
  isCall: boolean
}

const SOURCE_LABELS: Readonly<Record<ListingSource, string>> = {
  centrale_canine: 'Centrale Canine',
  chiens_de_france: 'Chiens de France',
  chiots_de_france: 'Chiots de France',
}

const SOURCE_LINK_LABELS: Readonly<Record<ListingSource, string>> = {
  centrale_canine: 'Voir sur la Centrale Canine',
  chiens_de_france: 'Voir sur Chiens de France',
  chiots_de_france: 'Voir sur Chiots de France',
}

/** How the detail screen and the desktop panel word a litter. */
export class LitterDetailPresentation {
  /**
   * The badge over the photo.
   *
   * @param litter - The litter.
   * @param today - Current day.
   * @returns « NÉE CETTE NUIT », « À NAÎTRE », or null.
   */
  static badge(litter: LitterCard, today: Date): string | null {
    if (litter.kind === 'litter_expected') {
      return 'À NAÎTRE'
    }
    if (litter.birth_date !== null && LitterPresentation.isLastNight(litter.birth_date, today)) {
      return 'NÉE CETTE NUIT'
    }
    return null
  }

  /**
   * The place line under the name.
   *
   * @param litter - The litter.
   * @returns « Redon, Ille-et-Vilaine », or the department alone.
   */
  static placeLine(litter: LitterCard): string {
    const parts: string[] = [litter.town, litter.department_name].filter(
      (part: string | null): part is string => part !== null,
    )
    return parts.length > 0 ? parts.join(', ') : 'Lieu à confirmer'
  }

  /**
   * The tier label under the score.
   *
   * @param litter - The litter.
   * @returns « préférée », « acceptable »…
   */
  static tierLabel(litter: LitterCard): string {
    switch (litter.tier) {
      case 'preferred':
        return 'préférée'
      case 'acceptable':
        return 'acceptable'
      case 'ignored':
        return 'ignorée'
      case 'excluded':
        return 'exclue'
      default:
        return 'à évaluer'
    }
  }

  /**
   * The three key facts.
   *
   * @param litter - The litter.
   * @returns Birth (or expected birth), puppies, departure.
   */
  static keyFacts(litter: LitterCard): LitterKeyFact[] {
    const birth: LitterKeyFact =
      litter.kind === 'litter_expected'
        ? {
            label: 'Naissance',
            value: litter.expected_birth_date
              ? `vers le ${LitterPresentation.shortDay(litter.expected_birth_date)}`
              : 'À confirmer',
            compactValue: litter.expected_birth_date
              ? LitterPresentation.shortDay(litter.expected_birth_date)
              : 'À confirmer',
          }
        : {
            label: 'Née le',
            value: litter.birth_date ? LitterPresentation.longDay(litter.birth_date) : 'À confirmer',
            compactValue: litter.birth_date ? LitterPresentation.shortDay(litter.birth_date) : 'À confirmer',
          }
    const puppies: string = LitterPresentation.sexLine(litter)
    const departure: LitterKeyFact = {
      label: 'Départ',
      value: litter.available_from ? `vers le ${LitterPresentation.shortDay(litter.available_from)}` : 'À confirmer',
      compactValue: litter.available_from ? LitterPresentation.shortDay(litter.available_from) : 'À confirmer',
    }
    return [birth, { label: 'Chiots', value: puppies, compactValue: puppies }, departure]
  }

  /**
   * The « Vu sur » line of a listing.
   *
   * @param listing - The listing.
   * @returns « Centrale Canine · déclaration de naissance ».
   */
  static sourceLine(listing: LitterSourceListing): string {
    const what: string =
      listing.kind === 'litter_expected'
        ? 'déclaration de saillie'
        : listing.kind === 'litter_born'
          ? 'déclaration de naissance'
          : 'annonce'
    return `${SOURCE_LABELS[listing.source]} · ${what}`
  }

  /**
   * Where the primary button leads: the breeder's phone when known, else the litter on its source.
   *
   * @param litter - The litter.
   * @returns The link and its label, or null when nothing is known.
   */
  static primaryAction(litter: LitterDetail): LitterPrimaryAction | null {
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
        label: SOURCE_LINK_LABELS[sourceListing.source],
        isCall: false,
      }
    }
    return null
  }
}
