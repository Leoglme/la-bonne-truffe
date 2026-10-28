import type { CockerCoat } from '~/constants/cockerCoatPalettes'
import type { CoatColor, LitterCard, LitterColor } from '~/types/api'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'

const LONG_MONTHS: readonly string[] = [
  'janvier',
  'février',
  'mars',
  'avril',
  'mai',
  'juin',
  'juillet',
  'août',
  'septembre',
  'octobre',
  'novembre',
  'décembre',
]

const SHORT_MONTHS: readonly string[] = [
  'janv.',
  'févr.',
  'mars',
  'avr.',
  'mai',
  'juin',
  'juil.',
  'août',
  'sept.',
  'oct.',
  'nov.',
  'déc.',
]

const NUMBER_WORDS: readonly string[] = ['Aucune', 'Une', 'Deux', 'Trois', 'Quatre', 'Cinq', 'Six', 'Sept', 'Huit']

/** Coats the illustration can paint; any other colour falls back to « couleur à confirmer ». */
const ILLUSTRATED_COATS: Readonly<Partial<Record<CoatColor, CockerCoat>>> = {
  gold: 'gold',
  noir_et_feu: 'noir_et_feu',
  noir: 'noir',
  marron: 'marron',
  bleu_rouan: 'bleu_rouan',
}

/**
 * How a litter reads on screen: French dates, sexes, colour label, coat of the illustration.
 * An unknown fact is written as unknown, never filled in.
 */
export class LitterPresentation {
  /**
   * Parse an ISO day (`2026-10-27`) as a local calendar day.
   *
   * @param isoDay - Day from the API.
   * @returns The date at local midnight.
   */
  static parseDay(isoDay: string): Date {
    const [year, month, day]: number[] = isoDay.split('-').map(Number)
    return new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1)
  }

  /**
   * A day written in full, as on the detail screen.
   *
   * @param isoDay - Day from the API.
   * @returns « 27 octobre ».
   */
  static longDay(isoDay: string): string {
    const day: Date = this.parseDay(isoDay)
    return `${day.getDate()} ${LONG_MONTHS[day.getMonth()] ?? ''}`
  }

  /**
   * A day written short, as on the cards.
   *
   * @param isoDay - Day from the API.
   * @returns « 22 déc. ».
   */
  static shortDay(isoDay: string): string {
    const day: Date = this.parseDay(isoDay)
    return `${day.getDate()} ${SHORT_MONTHS[day.getMonth()] ?? ''}`
  }

  /**
   * Whether a day is today or yesterday: a litter born « cette nuit ».
   *
   * @param isoDay - Day from the API.
   * @param today - Current day.
   * @returns True for today or yesterday.
   */
  static isLastNight(isoDay: string, today: Date): boolean {
    const startOfToday: Date = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    const ageInDays: number = Math.round((startOfToday.getTime() - this.parseDay(isoDay).getTime()) / 86_400_000)
    return ageInDays >= 0 && ageInDays <= 1
  }

  /**
   * The coat the cocker illustration takes for a litter.
   *
   * @param colors - Colours of the litter.
   * @returns A known coat for a single certain colour, otherwise the « à confirmer » coat.
   */
  static coatOf(colors: readonly LitterColor[]): CockerCoat {
    const firstColor: LitterColor | undefined = colors[0]
    if (colors.length !== 1 || firstColor === undefined || firstColor.confidence === 'ambiguous') {
      return 'inconnue'
    }
    return ILLUSTRATED_COATS[firstColor.color] ?? 'inconnue'
  }

  /**
   * Label of the colour chip.
   *
   * @param colors - Colours of the litter.
   * @param isCompact - Phone and desktop say « À confirmer », the iPad « Couleur à confirmer ».
   * @returns « Gold », « Noir et feu »…
   */
  static colorLabel(colors: readonly LitterColor[], isCompact: boolean): string {
    const coat: CockerCoat = this.coatOf(colors)
    if (coat === 'inconnue') {
      return isCompact ? 'À confirmer' : 'Couleur à confirmer'
    }
    return COCKER_COAT_PALETTES[coat].label
  }

  /**
   * The colour as written in a sentence.
   *
   * @param colors - Colours of the litter.
   * @returns « gold », or « de couleur à confirmer ».
   */
  static colorInSentence(colors: readonly LitterColor[]): string {
    const coat: CockerCoat = this.coatOf(colors)
    return coat === 'inconnue' ? 'de couleur à confirmer' : COCKER_COAT_PALETTES[coat].label.toLowerCase()
  }

  /**
   * The sexes line of a card.
   *
   * @param card - The litter.
   * @returns « 2 ♂ · 3 ♀ », « 2 ♀ », « À naître » or « Sexes à confirmer ».
   */
  static sexLine(card: LitterCard): string {
    if (card.kind === 'litter_expected') {
      return 'À naître'
    }
    if (card.male_count === null || card.female_count === null) {
      return 'Sexes à confirmer'
    }
    const parts: string[] = []
    if (card.male_count > 0) {
      parts.push(`${card.male_count} ♂`)
    }
    if (card.female_count > 0) {
      parts.push(`${card.female_count} ♀`)
    }
    return parts.length > 0 ? parts.join(' · ') : 'Plus de chiot'
  }

  /**
   * The sexes in words, for the hero card and the notification-like sentences.
   *
   * @param card - The litter.
   * @returns « 2 mâles et 3 femelles », or null while unknown.
   */
  static sexSentence(card: LitterCard): string | null {
    if (card.male_count === null || card.female_count === null) {
      return null
    }
    const males: string = `${card.male_count} mâle${card.male_count > 1 ? 's' : ''}`
    const females: string = `${card.female_count} femelle${card.female_count > 1 ? 's' : ''}`
    return `${males} et ${females}`
  }

  /**
   * The place line of a card: town or department, then what matters next.
   *
   * @param card - The litter.
   * @returns « Redon », « Ploërmel · naissance vers le 7 nov. », « Ancenis · non LOF ».
   */
  static placeLine(card: LitterCard): string {
    const parts: string[] = [card.place ?? 'Lieu à confirmer']
    if (card.kind === 'litter_expected' && card.expected_birth_date) {
      parts.push(`naissance vers le ${this.shortDay(card.expected_birth_date)}`)
    }
    if (card.lof_status === 'non_lof') {
      parts.push('non LOF')
    }
    return parts.join(' · ')
  }

  /**
   * The greeting subtitle of the home screen.
   *
   * @param preferredCount - Litters at the « préférée » tier.
   * @param bornLastNightCount - Of those, litters born today or yesterday.
   * @returns « Trois portées te correspondent. Une est née cette nuit. »
   */
  static greetingSubtitle(preferredCount: number, bornLastNightCount: number): string {
    if (preferredCount === 0) {
      return 'Aucune portée ne te correspond pour l’instant. La truffe continue de chercher.'
    }
    const countWord: string = NUMBER_WORDS[preferredCount] ?? String(preferredCount)
    const correspond: string =
      preferredCount === 1 ? `${countWord} portée te correspond.` : `${countWord} portées te correspondent.`
    if (bornLastNightCount === 0) {
      return correspond
    }
    const bornWord: string = NUMBER_WORDS[bornLastNightCount] ?? String(bornLastNightCount)
    return bornLastNightCount === 1
      ? `${correspond} ${bornWord} est née cette nuit.`
      : `${correspond} ${bornWord} sont nées cette nuit.`
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
    return new Date(`${card.first_seen_at}Z`).getTime() > previousVisitAt.getTime()
  }
}
