import type { LitterCard, LitterColor } from '~/types/api'
import type { CockerCoat } from '~/types/CockerCoat'
import type { DevicePosition } from '~/types/Location'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { COCKER_COAT_PALETTES, ILLUSTRATED_COATS } from '~/constants/cockerCoatPalettes'
import { CrowFliesDistance } from '~/utils/crowFliesDistance'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'

const UNKNOWN_PLACE_LABEL: string = 'Lieu à confirmer'

/** How a litter reads on screen: colours, sexes, place, coat of the illustration; an unknown fact stays unknown. */
export class LitterPresentation {
  /**
   * Pick the coat the cocker illustration takes for a litter.
   *
   * @param colors - Colours of the litter.
   * @returns A known coat for a single certain colour, otherwise the « à confirmer » coat.
   */
  static resolveIllustrationCoat(colors: LitterColor[]): CockerCoat {
    const firstColor: LitterColor | undefined = colors[0]
    if (colors.length !== 1 || firstColor === undefined || firstColor.confidence === 'ambiguous') {
      return 'inconnue'
    }
    return ILLUSTRATED_COATS[firstColor.color] ?? 'inconnue'
  }

  /**
   * Pick the pastel background of the tile a litter is shown on.
   *
   * @param colors - Colours of the litter.
   * @returns The Tailwind class of its coat's tile.
   */
  static resolveTileClass(colors: LitterColor[]): string {
    return COCKER_COAT_PALETTES[this.resolveIllustrationCoat(colors)].tileClass
  }

  /**
   * Whether every colour of a litter is known: certain or confirmed, never a bundle of the source.
   *
   * @param colors - Colours of the litter.
   * @returns False with no colour, an ambiguous one or an unknown one.
   */
  static hasKnownColors(colors: LitterColor[]): boolean {
    return (
      colors.length > 0 &&
      colors.every(
        (reading: LitterColor): boolean => reading.confidence !== 'ambiguous' && reading.color !== 'inconnue',
      )
    )
  }

  /**
   * Build the label of the colour chip.
   *
   * @param colors - Colours of the litter.
   * @param isCompact - Phone and desktop say « À confirmer », the iPad « Couleur à confirmer ».
   * @returns « Gold », « Marron et feu », « Gold ou Noir et feu »…
   */
  static buildColorLabel(colors: LitterColor[], isCompact: boolean): string {
    if (!this.hasKnownColors(colors)) {
      return isCompact ? 'À confirmer' : 'Couleur à confirmer'
    }
    return colors.map((reading: LitterColor): string => COAT_COLOR_LABELS[reading.color]).join(' ou ')
  }

  /**
   * Build the colour as written inside a sentence.
   *
   * @param colors - Colours of the litter.
   * @returns « gold », « marron et feu », or « de couleur à confirmer ».
   */
  static buildColorPhrase(colors: LitterColor[]): string {
    if (!this.hasKnownColors(colors)) {
      return 'de couleur à confirmer'
    }
    return colors.map((reading: LitterColor): string => COAT_COLOR_LABELS[reading.color].toLowerCase()).join(' ou ')
  }

  /**
   * List the puppies of each sex in words, for sentences.
   *
   * @param card - The litter.
   * @returns « 2 mâles » and « 3 femelles », or nothing while the sexes are unknown.
   */
  static listSexCounts(card: LitterCard): string[] {
    if (card.male_count === null || card.female_count === null) {
      return []
    }
    return [
      `${card.male_count} ${FrenchText.pickForm(card.male_count, 'mâle', 'mâles')}`,
      `${card.female_count} ${FrenchText.pickForm(card.female_count, 'femelle', 'femelles')}`,
    ]
  }

  /**
   * Write how many puppies a litter still offers, when a source tells.
   *
   * @param card - The litter.
   * @returns « 2 chiots dispo », « 1 chiot dispo », « Plus aucun chiot dispo », or null while unknown or before the birth.
   */
  static buildPuppiesAvailableLabel(card: LitterCard): string | null {
    if (card.puppies_available === null || card.kind === 'litter_expected') {
      return null
    }
    if (card.puppies_available === 0) {
      return 'Plus aucun chiot dispo'
    }
    return `${card.puppies_available} ${FrenchText.pickForm(card.puppies_available, 'chiot dispo', 'chiots dispo')}`
  }

  /**
   * Whether the puppies left add something to the sexes of a card: fewer than the sexes count, or sexes unknown.
   *
   * @param card - The litter.
   * @returns True when the line of a card should say it.
   */
  static arePuppiesAvailableWorthTelling(card: LitterCard): boolean {
    if (card.puppies_available === null || card.kind === 'litter_expected') {
      return false
    }
    if (card.male_count === null || card.female_count === null) {
      return true
    }
    return card.puppies_available < card.male_count + card.female_count
  }

  /**
   * Build the place of a litter: its town, else its department.
   *
   * @param card - The litter.
   * @returns « Redon », « Ille-et-Vilaine » or « Lieu à confirmer ».
   */
  static buildPlace(card: LitterCard): string {
    return card.place ?? UNKNOWN_PLACE_LABEL
  }

  /**
   * Measure how far the breeding is from the person, when both positions are known.
   *
   * @param card - The litter.
   * @param position - Position of the device, null while unknown.
   * @returns The kilometres as the crow flies, or null.
   */
  static kilometersFromHome(card: LitterCard, position: DevicePosition | null): number | null {
    if (position === null || card.breeder_latitude === null || card.breeder_longitude === null) {
      return null
    }
    return CrowFliesDistance.kilometersBetween(position, {
      latitude: card.breeder_latitude,
      longitude: card.breeder_longitude,
    })
  }

  /**
   * Write how far the breeding is, for a line of a card.
   *
   * @param card - The litter.
   * @param position - Position of the device, null while unknown.
   * @returns « à 32 km », or null while either position is unknown.
   */
  static buildDistanceLabel(card: LitterCard, position: DevicePosition | null): string | null {
    const kilometers: number | null = this.kilometersFromHome(card, position)
    return kilometers === null ? null : CrowFliesDistance.buildLabel(kilometers)
  }

  /**
   * Build the place line of a card: the place, how far it is, then what matters next.
   *
   * @param card - The litter.
   * @param position - Position of the device, null while unknown.
   * @returns « Redon · à 32 km », « Ploërmel · naissance vers le 7 nov. », « Ancenis · non LOF ».
   */
  static buildPlaceLine(card: LitterCard, position: DevicePosition | null): string {
    const parts: string[] = [this.buildPlace(card)]
    const distanceLabel: string | null = this.buildDistanceLabel(card, position)
    if (distanceLabel !== null) {
      parts.push(distanceLabel)
    }
    if (card.kind === 'litter_expected' && card.expected_birth_date) {
      const expectedBirthDay: Date = FrenchDate.parseDay(card.expected_birth_date)
      parts.push(`naissance vers le ${FrenchDate.formatDayAndShortMonth(expectedBirthDay)}`)
    }
    if (card.lof_status === 'non_lof') {
      parts.push('non LOF')
    }
    return parts.join(' · ')
  }

  /**
   * Build the greeting subtitle of the home screen.
   *
   * @param preferredCount - Litters at the « préférée » tier.
   * @param bornLastNightCount - Of those, litters born today or yesterday.
   * @returns « Trois portées te correspondent. Une est née cette nuit. »
   */
  static buildGreetingSubtitle(preferredCount: number, bornLastNightCount: number): string {
    if (preferredCount === 0) {
      return 'Aucune portée ne te correspond pour l’instant. La truffe continue de chercher.'
    }
    const preferredWord: string = FrenchText.spellOutCount(preferredCount, 'feminine')
    const correspond: string = FrenchText.pickForm(preferredCount, 'portée te correspond', 'portées te correspondent')
    const preferredSentence: string = `${preferredWord} ${correspond}.`
    if (bornLastNightCount === 0) {
      return preferredSentence
    }
    const bornWord: string = FrenchText.spellOutCount(bornLastNightCount, 'feminine')
    const born: string = FrenchText.pickForm(bornLastNightCount, 'est née cette nuit', 'sont nées cette nuit')
    return `${preferredSentence} ${bornWord} ${born}.`
  }

  /**
   * Whether a litter was born today or yesterday: « née cette nuit ».
   *
   * @param card - The litter.
   * @param now - Current time.
   * @returns False for a litter to come or born earlier.
   */
  static isBornLastNight(card: LitterCard, now: Date): boolean {
    if (card.birth_date === null) {
      return false
    }
    const daysSinceBirth: number = FrenchDate.countDaysAgo(FrenchDate.parseDay(card.birth_date), now)
    return daysSinceBirth >= 0 && daysSinceBirth <= 1
  }

  /**
   * Whether a litter appeared after the previous visit (« Nouveau » badge).
   *
   * @param card - The litter.
   * @param previousVisitAt - Time of the previous visit, null on a first visit.
   * @returns True for a litter first seen after the previous visit.
   */
  static isNew(card: LitterCard, previousVisitAt: Date | null): boolean {
    if (previousVisitAt === null) {
      return false
    }
    return FrenchDate.parseApiDate(card.first_seen_at).getTime() > previousVisitAt.getTime()
  }
}
