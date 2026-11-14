import type {
  CoatColor,
  DogSex,
  ListingSource,
  LitterBreeder,
  LitterCard,
  LitterColor,
  LitterDetail,
  LitterSourceListing,
  MatchFlag,
  PuppyAdState,
} from '~/types/api'
import type { LitterDayFact, LitterDayFactKey, LitterKeyFact, LitterListingLine, LitterPuppyLine } from '~/types/Litter'
import type { LitterParentRole } from '~/types/LitterParentsList'
import type { DevicePosition, GeographicPoint, MapDestination } from '~/types/Location'
import type { PrimaryAction } from '~/types/PrimaryAction'
import type { UiPhotoViewerPhoto } from '~/types/UiPhotoViewer'
import {
  LISTING_KIND_LABELS,
  LISTING_SOURCE_LABELS,
  LISTING_SOURCE_LINK_LABELS,
  MATCH_FLAG_LABELS,
  PUPPY_AD_STATE_LABELS,
  PUPPY_SEX_LABELS,
} from '~/constants/litterLabels'
import { MAX_PARENT_RATING, PARENT_RATING_LABELS } from '~/constants/parentRatings'
import { FollowUpPresentation } from '~/utils/followUpPresentation'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'
import { GoldGeneticsPresentation } from '~/utils/goldGeneticsPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const UNKNOWN_FACT_LABEL: string = 'À confirmer'
const GONE_LISTING_LABEL: string = 'plus en ligne'
const GONE_PUPPY_LABEL: string = 'Plus en ligne'
const NEW_PHOTOS_BADGE_DAYS: number = 1
const SIREN_DIGIT_GROUP: RegExp = /(\d{3})(?=\d)/g
const FRENCH_COUNTRY_CODE: string = '+33'
const FRENCH_NATIONAL_NUMBER_LENGTH: number = 9
const PHONE_DIGIT_PAIR: RegExp = /(\d{2})(?=\d)/g

/** How the detail screen words a litter. */
export class LitterDetailPresentation {
  /**
   * Build the badge over the photo.
   *
   * @param litter - The litter.
   * @param now - Current time.
   * @returns « NÉE CETTE NUIT », « À NAÎTRE », « NOUVELLES PHOTOS · CE MATIN » the day new photos came and the next
   *   one, or null.
   */
  static buildPhotoBadge(litter: LitterDetail, now: Date): string | null {
    if (litter.kind === 'litter_expected') {
      return 'À NAÎTRE'
    }
    if (LitterPresentation.isBornLastNight(litter, now)) {
      return 'NÉE CETTE NUIT'
    }
    const photosAddedAt: string | null = litter.photos_added_at ?? null
    if (photosAddedAt === null) {
      return null
    }
    const addedAt: Date = FrenchDate.parseApiDate(photosAddedAt)
    if (FrenchDate.countDaysAgo(FrenchDate.startOfDay(addedAt), now) > NEW_PHOTOS_BADGE_DAYS) {
      return null
    }
    return `NOUVELLES PHOTOS · ${FrenchDate.formatRecentMoment(addedAt, now).toUpperCase()}`
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
   * @param now - Current time.
   * @returns Birth (or expected birth), puppies, departure.
   */
  static buildKeyFacts(litter: LitterCard, now: Date = new Date()): LitterKeyFact[] {
    return [
      this.buildBirthFact(litter, now),
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
   * Build the cards of « Vu sur »: one per listing, and a single one per source for its puppy ads.
   *
   * @param litter - The litter.
   * @returns The lines, in the order of the API; the puppy ads of a source where its first one stands.
   */
  static buildListingLines(litter: LitterDetail): LitterListingLine[] {
    const puppyAdsBySource: Map<ListingSource, LitterSourceListing[]> = new Map()
    this.listPuppyAds(litter.listings).forEach((listing: LitterSourceListing): void => {
      puppyAdsBySource.set(listing.source, [...(puppyAdsBySource.get(listing.source) ?? []), listing])
    })
    const lines: LitterListingLine[] = []
    litter.listings.forEach((listing: LitterSourceListing, index: number): void => {
      const key: string = `${listing.source}-${index}`
      if (listing.kind !== 'puppy_ad') {
        lines.push({
          key,
          href: listing.external_url,
          label: 'Vu sur',
          description: this.joinKnownParts([
            this.buildSourceLine(listing),
            listing.is_active ? null : GONE_LISTING_LABEL,
          ]),
          thumbnailUrl: null,
          isGone: !listing.is_active,
        })
        return
      }
      const sourcePuppyAds: LitterSourceListing[] = puppyAdsBySource.get(listing.source) ?? []
      if (sourcePuppyAds[0] === listing) {
        lines.push(this.buildPuppyAdsLine(key, listing.source, sourcePuppyAds))
      }
    })
    return lines
  }

  /**
   * Build the rows of « Les chiots »: one per puppy ad, its photo, its sex, its colour and where it stands. Its colour
   * is the one noted by hand, else the one its ad gives for sure, else the gold when both parents only give the gold.
   *
   * @param litter - The litter.
   * @returns « Chiot 1 · mâle · Disponible · 1 400 € »…, in the order of the API.
   */
  static buildPuppyLines(litter: LitterDetail): LitterPuppyLine[] {
    const puppyAds: LitterSourceListing[] = this.listPuppyAds(litter.listings)
    const everyPuppyColor: CoatColor | null = GoldGeneticsPresentation.isEveryPuppyGold(litter.gold_puppy_odds ?? null)
      ? 'gold'
      : null
    return puppyAds.map((listing: LitterSourceListing, puppyIndex: number): LitterPuppyLine => {
      const sex: DogSex = this.readPuppySex(listing)
      const onlyColor: LitterColor | undefined = listing.colors.length === 1 ? listing.colors[0] : undefined
      const statedColor: CoatColor | null =
        onlyColor !== undefined && onlyColor.confidence !== 'ambiguous' && onlyColor.color !== 'inconnue'
          ? onlyColor.color
          : null
      const notedColor: CoatColor | null = listing.confirmed_color ?? null
      return {
        key: `${listing.source}-${puppyIndex}`,
        listingId: listing.id,
        href: listing.external_url,
        label: this.buildPuppyLabel(puppyIndex, puppyAds.length),
        sex,
        sexLabel: sex === 'unknown' ? null : PUPPY_SEX_LABELS[sex].toLowerCase(),
        color: notedColor ?? onlyColor?.color ?? everyPuppyColor,
        knownColor: notedColor ?? statedColor ?? everyPuppyColor,
        stateLabel: this.buildPuppyStateLabel(listing, sex),
        isAvailable: listing.puppy_state === 'available',
        photoUrl: listing.photos[0] ?? null,
        isGone: !listing.is_active,
      }
    })
  }

  /**
   * Say where the puppy ads were seen last, beside the title of « Les chiots ».
   *
   * @param listings - The listings of the litter.
   * @param now - Current time.
   * @returns « Sur Chiens de France, ce matin » when they all come from one source, « Vus hier » otherwise, or null
   *   without puppy ads.
   */
  static buildPuppiesCaption(listings: LitterSourceListing[], now: Date): string | null {
    const puppyAds: LitterSourceListing[] = this.listPuppyAds(listings)
    const firstPuppyAd: LitterSourceListing | undefined = puppyAds[0]
    if (firstPuppyAd === undefined) {
      return null
    }
    const lastSeenAt: Date = new Date(
      Math.max(
        ...puppyAds.map((listing: LitterSourceListing): number =>
          FrenchDate.parseApiDate(listing.last_seen_at).getTime(),
        ),
      ),
    )
    const seenMoment: string = FrenchDate.formatRecentMoment(lastSeenAt, now)
    const isFromOneSource: boolean = puppyAds.every(
      (listing: LitterSourceListing): boolean => listing.source === firstPuppyAd.source,
    )
    return isFromOneSource ? `Sur ${LISTING_SOURCE_LABELS[firstPuppyAd.source]}, ${seenMoment}` : `Vus ${seenMoment}`
  }

  /**
   * Build the photos of the full-screen viewer, each captioned with the puppy its ad shows.
   *
   * @param litter - The litter.
   * @returns The photos, « Chiot 2 · Femelle » under those of a puppy ad.
   */
  static buildViewerPhotos(litter: LitterDetail): UiPhotoViewerPhoto[] {
    const puppyAds: LitterSourceListing[] = this.listPuppyAds(litter.listings)
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
   * List what the breeder has to confirm: the unknown facts that kept the litter below « préférée ».
   *
   * @param litter - The litter.
   * @returns « À confirmer avec l’éleveur : le LOF, les sexes », never the sexes of a litter to come, or null when
   *   nothing is unknown.
   */
  static buildFactsToConfirmLine(litter: LitterDetail): string | null {
    const facts: string[] = litter.flags
      .filter((flag: MatchFlag): boolean => flag !== 'sex_unknown' || litter.kind !== 'litter_expected')
      .map((flag: MatchFlag): string | null => MATCH_FLAG_LABELS[flag])
      .filter((fact: string | null): fact is string => fact !== null)
    return facts.length > 0 ? `À confirmer avec l’éleveur : ${facts.join(', ')}` : null
  }

  /**
   * Name the breeder: its affix, and the name the source gives when it differs.
   *
   * @param breeder - The breeder.
   * @returns « Du Clos de l'Élevage A », « Du Clos de l'Élevage A · Élevage Dupont », or null when nothing names it.
   */
  static buildBreederName(breeder: LitterBreeder): string | null {
    const affix: string | null = breeder.affix || null
    const displayName: string | null = breeder.display_name || null
    if (affix !== null && displayName !== null && affix.toLowerCase() !== displayName.toLowerCase()) {
      return `${affix} · ${displayName}`
    }
    return affix ?? displayName
  }

  /**
   * Build the line under the breeder's name: its town and its SIREN.
   *
   * @param breeder - The breeder.
   * @returns « Saint-Aubin-du-Cormier · SIREN 123 456 789 », or null when neither is known.
   */
  static buildBreederDetailsLine(breeder: LitterBreeder): string | null {
    const siren: string | null = breeder.siren ? `SIREN ${breeder.siren.replace(SIREN_DIGIT_GROUP, '$1 ')}` : null
    const line: string = this.joinKnownParts([breeder.city, siren])
    return line === '' ? null : line
  }

  /**
   * Write the phone of the breeder the French way.
   *
   * @param phoneE164 - The number, international format.
   * @returns « 06 79 84 65 55 » for a French number, the number unchanged otherwise.
   */
  static buildBreederPhoneLabel(phoneE164: string): string {
    const nationalNumber: string = phoneE164.slice(FRENCH_COUNTRY_CODE.length)
    if (!phoneE164.startsWith(FRENCH_COUNTRY_CODE) || nationalNumber.length !== FRENCH_NATIONAL_NUMBER_LENGTH) {
      return phoneE164
    }
    return `0${nationalNumber}`.replace(PHONE_DIGIT_PAIR, '$1 ')
  }

  /**
   * Pick where the primary button leads: the breeder's phone when known, else the litter on its source.
   *
   * @param litter - The litter.
   * @returns The link and its label, or null when nothing is known.
   */
  static resolvePrimaryAction(litter: LitterDetail): PrimaryAction | null {
    const phone: string | null = litter.breeder?.phone_e164 ?? null
    if (phone !== null) {
      return { href: `tel:${phone}`, label: 'Appeler l’éleveur', isCall: true }
    }
    const sourceListing: LitterSourceListing | undefined = litter.listings.find(
      (listing: LitterSourceListing): boolean => listing.external_url !== null,
    )
    if (sourceListing?.external_url) {
      return {
        href:
          sourceListing.kind === 'puppy_ad'
            ? this.buildLitterPageUrl(sourceListing.external_url)
            : sourceListing.external_url,
        label: LISTING_SOURCE_LINK_LABELS[sourceListing.source],
        isCall: false,
      }
    }
    return null
  }

  /**
   * List the puppy ads of a litter, one per puppy, in the order of the API.
   *
   * @param listings - The listings of the litter.
   * @returns Those of kind « annonce ».
   */
  private static listPuppyAds(listings: LitterSourceListing[]): LitterSourceListing[] {
    return listings.filter((listing: LitterSourceListing): boolean => listing.kind === 'puppy_ad')
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
    const sex: DogSex = this.readPuppySex(listing)
    if (sex !== 'unknown') {
      parts.push(PUPPY_SEX_LABELS[sex])
    }
    if (LitterPresentation.hasKnownColors(listing.colors)) {
      parts.push(LitterPresentation.buildColorLabel(listing.colors, true))
    }
    return parts.length > 0 ? parts.join(' · ') : null
  }

  /**
   * Read the sex of the puppy of an ad, from the counts the ad gives.
   *
   * @param listing - The puppy ad.
   * @returns « male » or « female », « unknown » when the ad does not tell.
   */
  private static readPuppySex(listing: LitterSourceListing): DogSex {
    if (listing.male_count === 1 && listing.female_count === 0) {
      return 'male'
    }
    if (listing.female_count === 1 && listing.male_count === 0) {
      return 'female'
    }
    return 'unknown'
  }

  /**
   * Say where the puppy of an ad stands: free and at what price, reserved, sold, or gone from its source.
   *
   * @param listing - The puppy ad.
   * @param sex - Its sex, as French agrees with it.
   * @returns « Disponible · 1 400 € », « Réservée », « Vendu », « Plus en ligne », or null when nothing tells it.
   */
  private static buildPuppyStateLabel(listing: LitterSourceListing, sex: DogSex): string | null {
    const state: PuppyAdState | null = listing.puppy_state ?? null
    if (state === 'available') {
      const priceCents: number | null = listing.price_cents ?? null
      return priceCents === null ? 'Disponible' : `Disponible · ${LitterPresentation.formatPrice(priceCents)}`
    }
    if (state !== null) {
      return PUPPY_AD_STATE_LABELS[state][sex === 'female' ? 'feminine' : 'masculine']
    }
    return listing.is_active ? null : GONE_PUPPY_LABEL
  }

  /**
   * Build the « Vu sur » line of the puppy ads of a source: how many puppies it shows, and a link to the page of the
   * litter that holds the first ad.
   *
   * @param key - Key of the line.
   * @param source - The source.
   * @param puppyAds - Its puppy ads, at least one.
   * @returns « Sites d’élevage (Chiens de France) · 3 chiots en photo ».
   */
  private static buildPuppyAdsLine(
    key: string,
    source: ListingSource,
    puppyAds: LitterSourceListing[],
  ): LitterListingLine {
    const isGone: boolean = puppyAds.every((listing: LitterSourceListing): boolean => !listing.is_active)
    const photographedCount: number = puppyAds.filter(
      (listing: LitterSourceListing): boolean => listing.photos.length > 0,
    ).length
    const puppiesLabel: string =
      photographedCount > 0
        ? `${photographedCount} ${FrenchText.pickForm(photographedCount, 'chiot en photo', 'chiots en photo')}`
        : `${puppyAds.length} ${FrenchText.pickForm(puppyAds.length, 'annonce de chiot', 'annonces de chiots')}`
    const firstPuppyAdUrl: string | null =
      puppyAds.find((listing: LitterSourceListing): boolean => listing.external_url !== null)?.external_url ?? null
    return {
      key,
      href: firstPuppyAdUrl === null ? null : this.buildLitterPageUrl(firstPuppyAdUrl),
      label: 'Vu sur',
      description: this.joinKnownParts([
        LISTING_SOURCE_LABELS[source],
        puppiesLabel,
        isGone ? GONE_LISTING_LABEL : null,
      ]),
      thumbnailUrl: null,
      isGone,
    }
  }

  /**
   * Find the page of a litter from the address of one of its puppy ads: a breeder's site shows every puppy of a
   * litter on one page, and the address of a puppy points at its number with a fragment (« #:~:text=2211562 »).
   *
   * @param puppyAdUrl - The address of a puppy ad.
   * @returns The address without its fragment: the page of the whole litter on a breeder's site, the page of the
   *   puppy on a site that gives each puppy its own.
   */
  private static buildLitterPageUrl(puppyAdUrl: string): string {
    return puppyAdUrl.split('#')[0] ?? puppyAdUrl
  }

  /**
   * Build the birth fact: the expected day for a litter to come, the birth day otherwise.
   *
   * @param litter - The litter.
   * @param now - Current time.
   * @returns « Naissance vers le 7 nov. », « Attendue le 5 octobre » once that day is past, or « Née le 27 octobre ».
   */
  private static buildBirthFact(litter: LitterCard, now: Date): LitterDayFact {
    if (
      litter.kind === 'litter_expected' &&
      litter.expected_birth_date &&
      FollowUpPresentation.isBirthOverdue(litter, now)
    ) {
      const expectedBirthDay: Date = FrenchDate.parseDay(litter.expected_birth_date)
      return {
        key: 'birth',
        label: 'Attendue le',
        value: FrenchDate.formatDayAndLongMonth(expectedBirthDay),
        compactValue: FrenchDate.formatDayAndShortMonth(expectedBirthDay),
      }
    }
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
   * @returns « vers le 22 déc. » on the iPad, « 22 déc. » on the phone and in the aside of the desktop.
   */
  private static buildApproximateDayFact(key: LitterDayFactKey, label: string, isoDay: string | null): LitterDayFact {
    if (isoDay === null) {
      return { key, label, value: UNKNOWN_FACT_LABEL, compactValue: UNKNOWN_FACT_LABEL }
    }
    const shortDay: string = FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(isoDay))
    return { key, label, value: `vers le ${shortDay}`, compactValue: shortDay }
  }

  /**
   * Name the Centrale Canine rating of a parent, agreed with its sex.
   *
   * @param rating - Rating from 1 to 6.
   * @param role - Father or mother.
   * @returns « Recommandée » for a mother rated 4; a level outside the grid keeps its number.
   */
  static buildParentRatingLabel(rating: number, role: LitterParentRole): string {
    return PARENT_RATING_LABELS[rating]?.[role] ?? `Niveau ${rating} sur ${MAX_PARENT_RATING}`
  }
}
