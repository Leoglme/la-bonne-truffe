import type { LitterCard, LitterDetail, LitterSourceListing } from '~/types/api'
import type {
  LitterDayFact,
  LitterDayFactKey,
  LitterKeyFact,
  LitterListingLine,
  LitterPrimaryAction,
} from '~/types/Litter'
import type { DevicePosition, GeographicPoint, MapDestination } from '~/types/Location'
import type { UiPhotoViewerPhoto } from '~/types/UiPhotoViewer'
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
   * Build the place line under the name: the town and its department, then how far it is.
   *
   * @param litter - The litter.
   * @param position - Position of the device, null while unknown.
   * @returns « Redon, Ille-et-Vilaine · à 32 km », or the department alone.
   */
  static buildTownAndDepartment(litter: LitterCard, position: DevicePosition | null): string {
    const distanceLabel: string | null = LitterPresentation.buildDistanceLabel(litter, position)
    return this.joinKnownParts([this.buildPlaceName(litter), distanceLabel])
  }

  /**
   * Pick where the map apps take the person: the breeding itself when its position is known, else its place.
   *
   * @param litter - The litter.
   * @returns The destination, or null while neither the position nor the place is known.
   */
  static buildMapDestination(litter: LitterCard): MapDestination | null {
    const hasKnownPlace: boolean = litter.town !== null || litter.department_name !== null
    const point: GeographicPoint | null =
      litter.breeder_latitude !== null && litter.breeder_longitude !== null
        ? { latitude: litter.breeder_latitude, longitude: litter.breeder_longitude }
        : null
    if (point === null && !hasKnownPlace) {
      return null
    }
    return { point, placeName: this.buildPlaceName(litter) }
  }

  /**
   * Name the place of a litter: the town and its department.
   *
   * @param litter - The litter.
   * @returns « Redon, Ille-et-Vilaine », the department alone, or « Lieu à confirmer ».
   */
  private static buildPlaceName(litter: LitterCard): string {
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
    return [
      this.buildBirthFact(litter),
      { key: 'puppies', label: 'Chiots' },
      this.buildApproximateDayFact('departure', 'Départ', litter.available_from),
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
   * Build the cards of the listings: one per puppy ad, « Chiot 1 », « Chiot 2 »…, and « Vu sur » for the others.
   *
   * @param litter - The litter.
   * @returns One line per listing, in the order of the API.
   */
  static buildListingLines(litter: LitterDetail): LitterListingLine[] {
    const puppyAds: LitterSourceListing[] = this.listPuppyAds(litter)
    return litter.listings.map((listing: LitterSourceListing, index: number): LitterListingLine => {
      const key: string = `${listing.source}-${index}`
      if (listing.kind !== 'puppy_ad') {
        return {
          key,
          href: listing.external_url,
          label: 'Vu sur',
          description: this.buildSourceLine(listing),
          thumbnailUrl: null,
        }
      }
      return {
        key,
        href: listing.external_url,
        label: this.buildPuppyLabel(puppyAds.indexOf(listing), puppyAds.length),
        description: this.joinKnownParts([this.buildPuppyDescription(listing), LISTING_SOURCE_LABELS[listing.source]]),
        thumbnailUrl: listing.photos[0] ?? null,
      }
    })
  }

  /**
   * Build the photos of the full-screen viewer, each captioned with the puppy its ad shows.
   *
   * @param litter - The litter.
   * @returns The photos, « Chiot 2 · Femelle » under those of a puppy ad.
   */
  static buildViewerPhotos(litter: LitterDetail): UiPhotoViewerPhoto[] {
    const puppyAds: LitterSourceListing[] = this.listPuppyAds(litter)
    return litter.photos.map((url: string): UiPhotoViewerPhoto => {
      const puppyIndex: number = puppyAds.findIndex((listing: LitterSourceListing): boolean =>
        listing.photos.includes(url),
      )
      const puppyAd: LitterSourceListing | undefined = puppyAds[puppyIndex]
      if (puppyAd === undefined) {
        return { url, caption: null }
      }
      return {
        url,
        caption: this.joinKnownParts([
          this.buildPuppyLabel(puppyIndex, puppyAds.length),
          this.buildPuppyDescription(puppyAd),
        ]),
      }
    })
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
   * List the puppy ads of a litter, one per puppy, in the order of the API.
   *
   * @param litter - The litter.
   * @returns Its listings of kind « annonce ».
   */
  private static listPuppyAds(litter: LitterDetail): LitterSourceListing[] {
    return litter.listings.filter((listing: LitterSourceListing): boolean => listing.kind === 'puppy_ad')
  }

  /**
   * Join the parts of a line that are known.
   *
   * @param parts - The parts, null when unknown.
   * @returns « Chiot 1 · Mâle · Chiens de France ».
   */
  private static joinKnownParts(parts: (string | null)[]): string {
    return parts.filter((part: string | null): part is string => part !== null).join(' · ')
  }

  /**
   * Name a puppy by its ad: numbered when the litter has several puppy ads.
   *
   * @param puppyIndex - Position of the ad among the puppy ads of the litter.
   * @param puppyCount - Number of puppy ads of the litter.
   * @returns « Chiot 2 », or « Chiot » when it is the only one.
   */
  private static buildPuppyLabel(puppyIndex: number, puppyCount: number): string {
    return puppyCount > 1 ? `Chiot ${puppyIndex + 1}` : 'Chiot'
  }

  /**
   * Describe the puppy of an ad: its sex and its colour, when the ad tells them.
   *
   * @param listing - The puppy ad.
   * @returns « Mâle · Gold », « Femelle », or null when the ad tells neither.
   */
  private static buildPuppyDescription(listing: LitterSourceListing): string | null {
    const parts: string[] = []
    if (listing.male_count === 1 && listing.female_count === 0) {
      parts.push('Mâle')
    } else if (listing.female_count === 1 && listing.male_count === 0) {
      parts.push('Femelle')
    }
    if (LitterPresentation.hasKnownColors(listing.colors)) {
      parts.push(LitterPresentation.buildColorLabel(listing.colors, true))
    }
    return parts.length > 0 ? parts.join(' · ') : null
  }

  /**
   * Build the birth fact: the expected day for a litter to come, the birth day otherwise.
   *
   * @param litter - The litter.
   * @returns « Naissance vers le 7 nov. » or « Née le 27 octobre ».
   */
  private static buildBirthFact(litter: LitterCard): LitterDayFact {
    if (litter.kind === 'litter_expected') {
      return this.buildApproximateDayFact('birth', 'Naissance', litter.expected_birth_date)
    }
    if (litter.birth_date === null) {
      return { key: 'birth', label: 'Née le', value: UNKNOWN_FACT_LABEL, compactValue: UNKNOWN_FACT_LABEL }
    }
    const birthDay: Date = FrenchDate.parseDay(litter.birth_date)
    return {
      key: 'birth',
      label: 'Née le',
      value: FrenchDate.formatDayAndLongMonth(birthDay),
      compactValue: FrenchDate.formatDayAndShortMonth(birthDay),
    }
  }

  /**
   * Build a fact that holds an approximate day.
   *
   * @param key - Which fact it is.
   * @param label - « Naissance » or « Départ ».
   * @param isoDay - The day from the API, null while unknown.
   * @returns « vers le 22 déc. » on the iPad, « 22 déc. » on the phone and the panel.
   */
  private static buildApproximateDayFact(key: LitterDayFactKey, label: string, isoDay: string | null): LitterDayFact {
    if (isoDay === null) {
      return { key, label, value: UNKNOWN_FACT_LABEL, compactValue: UNKNOWN_FACT_LABEL }
    }
    const shortDay: string = FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(isoDay))
    return { key, label, value: `vers le ${shortDay}`, compactValue: shortDay }
  }
}
