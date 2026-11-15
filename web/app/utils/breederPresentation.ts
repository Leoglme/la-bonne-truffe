import type {
  BreederCard,
  BreederColorShare,
  BreederDetail,
  BreederDog,
  BreederFilter,
  BreederFollow,
  BreederLink,
  BreederLinkPreview,
  BreederSiteLitter,
  BreederSocialAccount,
  LitterCard,
  ProbableLitter,
  SocialLinkOrigin,
} from '~/types/api'
import type {
  BreederChip,
  BreederColorShareSlice,
  BreederKeyFact,
  BreederLinkRecognition,
  BreederLitterStatusLine,
  BreederSeenOnLink,
  BreederSiteLink,
  BreederSiteLittersYear,
  BreederSocialAccountKind,
  BreederSocialAccountRecognition,
  ProbableLitterLine,
} from '~/types/Breeder'
import type { FrenchGender } from '~/types/FrenchText'
import type { DevicePosition } from '~/types/Location'
import type { PrimaryAction } from '~/types/PrimaryAction'
import type { LinkLogo, LinkLogoImage } from '~/types/UiLinkLogo'
import {
  BREEDER_DOGS_SHOWN_COUNT,
  COAT_COLOR_SWATCHES,
  SOCIAL_ACCOUNT_LABELS,
  SOCIAL_ACCOUNT_RECOGNITIONS,
  SOCIAL_LINK_ORIGIN_LABELS,
} from '~/constants/breederOptions'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { LINK_LOGOS_BY_DOMAIN } from '~/constants/linkLogos'
import { UNKNOWN_PLACE_LABEL } from '~/constants/litterLabels'
import { CrowFliesDistance } from '~/utils/crowFliesDistance'
import { FollowUpPresentation } from '~/utils/followUpPresentation'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'
import { GoldGeneticsPresentation } from '~/utils/goldGeneticsPresentation'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const INITIALS_SKIPPED_WORDS: Set<string> = new Set(['de', 'des', 'du', 'd', 'la', 'le', 'les', 'l', 'et', 'au', 'aux'])
const HOT_BIRTH_AGE_DAYS: number = 7
const INACTIVE_AFTER_DAYS: number = 2 * 365
const SIREN_DIGIT_GROUP: RegExp = /(\d{3})(?=\d)/g
const E_LOCUS_CODE_PATTERN: RegExp = /^LocE\w*-/
const ADDRESS_SCHEME_AND_WWW: RegExp = /^https?:\/\/(www\.)?/i
const ADDRESS_LAST_SLASH: RegExp = /\/$/
const WORD_JOINER: string = '\u2060'
const NO_BREAK_SPACE: string = '\u00a0'
const MONTH_AND_YEAR_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' })
const MONTH_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat('fr-FR', { month: 'long' })
const SMALL_BREEDING_MOST_FEMALES: number = 4
const LARGE_BREEDING_LEAST_FEMALES: number = 10
const SMALL_BREEDING_MOST_LITTERS: number = 3
const LARGE_BREEDING_LEAST_LITTERS: number = 9
const YEARLY_GAP_LEAST_MONTHS: number = 10
const YEARLY_GAP_MOST_MONTHS: number = 14
const YEARLY_LITTERS_PER_MOTHER_LEAST: number = 0.8
const YEARLY_LITTERS_PER_MOTHER_MOST: number = 1.2
const DAYS_IN_A_YEAR: number = 365

/** How the breeder screens word a breeder: its place, its litters, its chips and its follow. */
export class BreederPresentation {
  /**
   * Whether a card belongs to a filtered list.
   *
   * @param card - The breeder.
   * @param filter - The chip chosen.
   * @returns True when the card is listed.
   */
  static passesFilter(card: BreederCard, filter: BreederFilter): boolean {
    if (filter === 'followed') {
      return card.is_followed
    }
    if (filter === 'gold') {
      return card.gold_litters_count > 0
    }
    if (filter === 'club') {
      return card.is_breed_club_member
    }
    if (filter === 'active_litter') {
      return card.current_litter !== null
    }
    if (filter === 'probable_litter') {
      return (card.next_probable_litter ?? null) !== null
    }
    return true
  }

  /**
   * Build the subtitle of the tab: how many breeders are listed, and how many are followed.
   *
   * @param cards - The breeders listed.
   * @returns « 38 élevages de cocker anglais dans tes départements. Tu en suis 3. »
   */
  static buildSubtitle(cards: BreederCard[]): string {
    const followedCount: number = cards.filter((card: BreederCard): boolean => card.is_followed).length
    const breedings: string = `${cards.length} ${FrenchText.pickForm(cards.length, 'élevage', 'élevages')} de cocker anglais dans tes départements.`
    if (followedCount === 0) {
      return breedings
    }
    return `${breedings} Tu en suis ${followedCount}.`
  }

  /**
   * The two letters of the tile of a breeder without a photo: the first letters of its significant words.
   *
   * @param name - The name of the breeding.
   * @returns « LT » for « Des Landes de Test », « AM » for « Ar Mor Test ».
   */
  static buildInitials(name: string): string {
    const significantWords: string[] = name
      .split(/[\s'’-]+/)
      .filter((word: string): boolean => word !== '' && !INITIALS_SKIPPED_WORDS.has(word.toLowerCase()))
    const words: string[] = significantWords.length > 0 ? significantWords : name.split(/\s+/)
    return words
      .slice(0, 2)
      .map((word: string): string => word.charAt(0).toUpperCase())
      .join('')
  }

  /**
   * The pastel of the tile of a breeder: gold for a gold breeding, coral for one added by hand.
   *
   * @param card - The breeder.
   * @returns Tailwind classes of the background and the text.
   */
  static resolveTileClass(card: BreederCard): string {
    if (card.gold_litters_count > 0) {
      return 'bg-gold-pastel text-gold-ink'
    }
    if (card.is_manual) {
      return 'bg-coral-pastel text-coral-text'
    }
    if (card.litters_count > 0) {
      return 'bg-lilac-pastel text-ink-secondary'
    }
    return 'bg-neutral-pastel text-ink-secondary'
  }

  /**
   * Build the place line of a breeder: its town and department, then how far it is.
   *
   * @param card - The breeder.
   * @param position - Position of the device, null while unknown.
   * @returns « Ploërmel, Morbihan · à 48 km », « Lieu à confirmer ».
   */
  static buildPlaceLine(card: BreederCard, position: DevicePosition | null): string {
    const place: string = [card.city, card.department_name]
      .filter((part: string | null): part is string => part !== null)
      .join(', ')
    const parts: string[] = [place === '' ? UNKNOWN_PLACE_LABEL : place]
    if (position !== null && card.latitude !== null && card.longitude !== null) {
      const kilometers: number = CrowFliesDistance.kilometersBetween(position, {
        latitude: card.latitude,
        longitude: card.longitude,
      })
      parts.push(CrowFliesDistance.buildLabel(kilometers))
    }
    return parts.join(' · ')
  }

  /**
   * Build the line under the name of the breeder page: the person, then the place.
   *
   * @param detail - The breeder.
   * @param position - Position of the device, null while unknown.
   * @returns « Marie Le Goff · Ploërmel, Morbihan · à 48 km ».
   */
  static buildIdentityLine(detail: BreederDetail, position: DevicePosition | null): string {
    return [detail.person_name, this.buildPlaceLine(detail, position)]
      .filter((part: string | null): part is string => part !== null)
      .join(' · ')
  }

  /**
   * Build the line that says where the breeder stands with its litters.
   *
   * @param card - The breeder.
   * @param now - Current time.
   * @returns « À naître vers le 7 nov. · gold », « Née le 14 sept. · gold, 2 ♂ et 3 ♀ », « Aucune portée depuis 2024 ».
   */
  static buildLitterStatusLine(card: BreederCard, now: Date): BreederLitterStatusLine {
    const litter: LitterCard | null = card.current_litter
    if (litter !== null) {
      return this.buildCurrentLitterLine(litter, now)
    }
    const lastLitterDay: Date | null = card.last_litter_date ? FrenchDate.parseDay(card.last_litter_date) : null
    if (card.litters_last_year_count !== null && card.litters_last_year_count > 0) {
      const rhythm: string = `${card.litters_last_year_count} ${FrenchText.pickForm(card.litters_last_year_count, 'portée', 'portées')} l’an dernier`
      return {
        text: lastLitterDay === null ? rhythm : `${rhythm} · dernière en ${MONTH_FORMAT.format(lastLitterDay)}`,
        tone: 'normal',
      }
    }
    if (lastLitterDay === null) {
      return { text: 'Aucune portée connue', tone: 'inactive' }
    }
    if (FrenchDate.countDaysAgo(lastLitterDay, now) > INACTIVE_AFTER_DAYS) {
      return { text: `Aucune portée depuis ${lastLitterDay.getFullYear()}`, tone: 'inactive' }
    }
    return { text: `Dernière portée en ${MONTH_AND_YEAR_FORMAT.format(lastLitterDay)}`, tone: 'normal' }
  }

  /**
   * Build the chips of a card: what the sources vouch for.
   *
   * @param card - The breeder.
   * @param isCompact - Short labels, for the narrow cards.
   * @returns The chips, in a stable order.
   */
  static listChips(card: BreederCard, isCompact: boolean): BreederChip[] {
    const chips: BreederChip[] = []
    if (card.is_selected_breeding) {
      chips.push({ label: isCompact ? 'Sélectionné' : 'Élevage sélectionné', tone: 'neutral' })
    }
    if (card.is_breed_club_member) {
      chips.push({ label: 'Spaniel Club', tone: 'neutral' })
    }
    if (card.has_chiens_de_france_site) {
      chips.push({ label: 'Site Chiens de France', tone: 'neutral' })
    }
    if (card.gold_litters_count > 0 && card.gold_litters_count * 2 >= card.litters_count) {
      chips.push({ label: 'Gold surtout', tone: 'gold' })
    }
    if (card.is_manual) {
      chips.push({ label: 'Ajouté à la main', tone: 'coral' })
    }
    return chips
  }

  /**
   * Build the chips of the breeder page: longer, with what the directories certify.
   *
   * @param detail - The breeder.
   * @returns The chips, in a stable order.
   */
  static listDetailChips(detail: BreederDetail): BreederChip[] {
    const chips: BreederChip[] = []
    if (detail.is_selected_breeding) {
      chips.push({ label: 'Élevage sélectionné', tone: 'neutral' })
    }
    if (detail.is_breed_club_member) {
      chips.push({ label: 'Membre du Spaniel Club Français', tone: 'neutral' })
    }
    if (detail.has_siren) {
      chips.push({ label: 'SIREN vérifié', tone: 'green' })
    }
    if (detail.chiens_de_france_registered_on) {
      const registeredOn: Date = FrenchDate.parseDay(detail.chiens_de_france_registered_on)
      chips.push({ label: `Sur Chiens de France depuis ${registeredOn.getFullYear()}`, tone: 'neutral' })
    } else if (detail.has_chiens_de_france_site) {
      chips.push({ label: 'Site Chiens de France', tone: 'neutral' })
    }
    if (detail.is_manual) {
      chips.push({ label: 'Ajouté à la main', tone: 'coral' })
    }
    return chips
  }

  /**
   * Build the lines of « En bref »: size, gold, rhythm and last litter, each left out when the sources say nothing.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns « Grand élevage : 18 chiennes, 13 portées par an », « Du gold dans 3 portées sur 3 »…
   */
  static listKeyFacts(detail: BreederDetail, now: Date): BreederKeyFact[] {
    return [
      this.buildSizeFact(detail, now),
      this.buildGoldFact(detail),
      this.buildRhythmFact(detail, now),
      this.buildLastLitterFact(detail, now),
    ].filter((fact: BreederKeyFact | null): fact is BreederKeyFact => fact !== null)
  }

  /**
   * Build the line a card shows for the soonest probable litter of a breeder.
   *
   * @param card - The breeder.
   * @param now - Current time.
   * @returns « Portée gold probable vers novembre », « Portée probable vers janvier 2027 », or null without one.
   */
  static buildProbableLitterLine(card: BreederCard, now: Date): string | null {
    const litter: ProbableLitter | null = card.next_probable_litter ?? null
    if (litter === null) {
      return null
    }
    const color: string = LitterPresentation.hasKnownColors(litter.colors)
      ? ` ${LitterPresentation.buildColorPhrase(litter.colors)}`
      : ''
    return `Portée${color} probable vers ${this.buildProbableMonth(litter, now)}`
  }

  /**
   * Build the rows of « Ses prochaines portées »: when, which mother, which colours.
   *
   * @param probableLitters - The probable litters of a breeder, the soonest first.
   * @param now - Current time.
   * @returns « Vers novembre » · « Mère : Selune · sa dernière portée est née le 19 nov. 2025 », in the same order.
   */
  static listProbableLitterLines(probableLitters: ProbableLitter[], now: Date): ProbableLitterLine[] {
    return probableLitters.map((litter: ProbableLitter): ProbableLitterLine => ({
      key: `${litter.dam_name}-${litter.last_litter_born_on}`,
      title: `Vers ${this.buildProbableMonth(litter, now)}`,
      motherLine: `Mère : ${litter.dam_name} · sa dernière portée est née le ${FrenchDate.formatDayAndShortMonthWithOtherYear(
        FrenchDate.parseDay(litter.last_litter_born_on),
        now,
      )}`,
      colors: litter.colors,
      hasKnownColors: LitterPresentation.hasKnownColors(litter.colors),
    }))
  }

  /**
   * Write the month a probable litter is expected, with its year when it is not the current one.
   *
   * @param litter - The probable litter.
   * @param now - Current time.
   * @returns « novembre », « janvier 2027 ».
   */
  private static buildProbableMonth(litter: ProbableLitter, now: Date): string {
    const expectedOn: Date = FrenchDate.parseDay(litter.expected_on)
    return expectedOn.getFullYear() === now.getFullYear()
      ? MONTH_FORMAT.format(expectedOn)
      : MONTH_AND_YEAR_FORMAT.format(expectedOn)
  }

  /**
   * Build the size of a breeding: small, medium or large by its mothers, else by its litters of a year.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns « Petit élevage : 4 chiennes, 3 portées par an », or null when neither is known.
   */
  private static buildSizeFact(detail: BreederDetail, now: Date): BreederKeyFact | null {
    const mothersCount: number | null = this.countMothers(detail)
    const littersCount: number | null = this.countLittersOfLastYear(detail, now)
    if (mothersCount === null && littersCount === null) {
      return null
    }
    const parts: string[] = []
    if (mothersCount !== null) {
      parts.push(`${mothersCount} ${FrenchText.pickForm(mothersCount, 'chienne', 'chiennes')}`)
    }
    if (littersCount !== null) {
      parts.push(`${littersCount} ${FrenchText.pickForm(littersCount, 'portée', 'portées')} par an`)
    }
    return {
      key: 'size',
      iconName: 'i-lucide-house',
      boldStart: this.resolveSizeLabel(mothersCount, littersCount),
      sentenceEnd: ` : ${parts.join(', ')}`,
    }
  }

  /**
   * Name the size of a breeding.
   *
   * @param mothersCount - Its mothers, null while unknown.
   * @param littersCount - Its litters of a year, null while unknown.
   * @returns « Petit élevage », « Élevage moyen » or « Grand élevage ».
   */
  private static resolveSizeLabel(mothersCount: number | null, littersCount: number | null): string {
    if (mothersCount !== null) {
      if (mothersCount <= SMALL_BREEDING_MOST_FEMALES) {
        return 'Petit élevage'
      }
      return mothersCount >= LARGE_BREEDING_LEAST_FEMALES ? 'Grand élevage' : 'Élevage moyen'
    }
    if (littersCount !== null && littersCount <= SMALL_BREEDING_MOST_LITTERS) {
      return 'Petit élevage'
    }
    return littersCount !== null && littersCount >= LARGE_BREEDING_LEAST_LITTERS ? 'Grand élevage' : 'Élevage moyen'
  }

  /**
   * Count the mothers of a breeding: the most of those it declares and of those its site shows among its dogs.
   *
   * @param detail - The breeder.
   * @returns Its mothers, null while neither is known.
   */
  private static countMothers(detail: BreederDetail): number | null {
    const shownOnSiteCount: number = detail.reproducers.filter(
      (dog: BreederDog): boolean => dog.sex === 'female' && dog.role === 'reproducer',
    ).length
    const mothersCount: number = Math.max(detail.breeding_females_count ?? 0, shownOnSiteCount)
    return mothersCount === 0 ? null : mothersCount
  }

  /**
   * Count the litters of a breeding over a year: the most of those it declares and of those its site shows.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns Its litters born in the last twelve months, null while neither is known.
   */
  private static countLittersOfLastYear(detail: BreederDetail, now: Date): number | null {
    const shownOnSiteCount: number = (detail.site_litters ?? []).filter((litter: BreederSiteLitter): boolean => {
      const daysAgo: number = FrenchDate.countDaysAgo(FrenchDate.parseDay(litter.birth_date), now)
      return daysAgo >= 0 && daysAgo < DAYS_IN_A_YEAR
    }).length
    const littersCount: number = Math.max(detail.litters_last_year_count ?? 0, shownOnSiteCount)
    return littersCount === 0 ? null : littersCount
  }

  /**
   * Build the gold of a breeding: in how many of its litters, else its main colour.
   *
   * @param detail - The breeder.
   * @returns « Du gold dans 3 portées sur 3 », « Pas de gold : surtout du bleu rouan », or null without a litter.
   */
  private static buildGoldFact(detail: BreederDetail): BreederKeyFact | null {
    if (detail.litters_count === 0) {
      return null
    }
    if (detail.gold_litters_count > 0) {
      const sentenceEnd: string =
        detail.litters_count === 1
          ? ' dans sa seule portée connue'
          : ` dans ${detail.gold_litters_count} ${FrenchText.pickForm(detail.gold_litters_count, 'portée', 'portées')} sur ${detail.litters_count}`
      return { key: 'gold', iconName: 'i-lucide-heart', boldStart: 'Du gold', sentenceEnd }
    }
    const mainShare: BreederColorShare | undefined = detail.color_shares[0]
    return {
      key: 'gold',
      iconName: 'i-lucide-heart',
      boldStart: 'Pas de gold',
      sentenceEnd: mainShare
        ? ` : surtout du ${COAT_COLOR_LABELS[mainShare.color].toLowerCase()}`
        : ' dans ses portées connues',
    }
  }

  /**
   * Build how often each mother has a litter, as « En bref » says it.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns « Une portée par an pour chaque chienne », « Une portée tous les 7 mois pour chaque chienne », or null.
   */
  private static buildRhythmFact(detail: BreederDetail, now: Date): BreederKeyFact | null {
    const rhythm: string | null = this.resolveRhythm(detail, now)
    return rhythm === null
      ? null
      : { key: 'rhythm', iconName: 'i-lucide-clock', boldStart: rhythm, sentenceEnd: ' pour chaque chienne' }
  }

  /**
   * Say how often each mother has a litter: the middle gap between two litters of one, else litters per mother.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns « Une portée par an », « Une portée tous les 7 mois », « Près de deux portées par an », or null.
   */
  private static resolveRhythm(detail: BreederDetail, now: Date): string | null {
    const gapMonths: number | null = detail.dam_litter_gap_months ?? null
    if (gapMonths !== null) {
      const isGapAboutAYear: boolean = gapMonths >= YEARLY_GAP_LEAST_MONTHS && gapMonths <= YEARLY_GAP_MOST_MONTHS
      return isGapAboutAYear ? 'Une portée par an' : `Une portée tous les ${gapMonths} mois`
    }
    const mothersCount: number | null = this.countMothers(detail)
    const littersCount: number | null = this.countLittersOfLastYear(detail, now)
    if (mothersCount === null || littersCount === null) {
      return null
    }
    const littersPerMother: number = littersCount / mothersCount
    if (littersPerMother > YEARLY_LITTERS_PER_MOTHER_MOST) {
      return 'Près de deux portées par an'
    }
    return littersPerMother < YEARLY_LITTERS_PER_MOTHER_LEAST ? null : 'Une portée par an'
  }

  /**
   * Build the last litter of a breeding, or the next one when it is announced.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns « Dernière portée le 22 oct. », « Prochaine portée vers le 23 déc. », or null without a litter.
   */
  private static buildLastLitterFact(detail: BreederDetail, now: Date): BreederKeyFact | null {
    if (!detail.last_litter_date) {
      return null
    }
    const day: Date = FrenchDate.parseDay(detail.last_litter_date)
    const dayLabel: string = FrenchDate.formatDayAndShortMonthWithOtherYear(day, now)
    if (FrenchDate.countDaysAgo(day, now) < 0) {
      return {
        key: 'last-litter',
        iconName: 'i-lucide-calendar',
        boldStart: 'Prochaine portée',
        sentenceEnd: ` vers le ${dayLabel}`,
      }
    }
    return {
      key: 'last-litter',
      iconName: 'i-lucide-calendar',
      boldStart: 'Dernière portée',
      sentenceEnd: ` le ${dayLabel}`,
    }
  }

  /**
   * Build the slices of the bar of « Ses couleurs ».
   *
   * @param detail - The breeder.
   * @returns One slice per colour known, the largest first, as the API orders them.
   */
  static buildColorShares(detail: BreederDetail): BreederColorShareSlice[] {
    const total: number = detail.color_shares.reduce(
      (sum: number, share: BreederColorShare): number => sum + share.litters_count,
      0,
    )
    if (total === 0) {
      return []
    }
    return detail.color_shares.map((share: BreederColorShare): BreederColorShareSlice => ({
      label: COAT_COLOR_LABELS[share.color],
      percent: Math.round((share.litters_count / total) * 100),
      swatch: COAT_COLOR_SWATCHES[share.color],
      littersCount: share.litters_count,
    }))
  }

  /**
   * Build the rows of « Vu sur »: each place the breeder is known from, with a link when there is one.
   *
   * @param detail - The breeder.
   * @param now - Current time.
   * @returns The rows, the directories first, then the sites and the social accounts with where each link comes
   *   from, then what was added by hand.
   */
  static listSeenOnLinks(detail: BreederDetail, now: Date): BreederSeenOnLink[] {
    const links: BreederSeenOnLink[] = []
    if (detail.scc_breeder_id !== null) {
      const facts: string[] = [detail.affix ? 'Affixe déposé' : 'Éleveur déclaré']
      if (detail.siren) {
        facts.push(`SIREN ${detail.siren.replace(SIREN_DIGIT_GROUP, '$1 ')}`)
      }
      links.push({
        key: 'scc',
        logo: 'centrale_canine',
        label: 'Centrale Canine',
        description: facts.join(' · '),
        href: null,
      })
    }
    if (detail.chiens_de_france_site_url !== null) {
      const siteReadAt: string | null = detail.chiens_de_france_site_seen_at ?? null
      links.push({
        key: 'chiens-de-france',
        logo: 'chiens_de_france',
        label: 'Chiens de France',
        description: `Site de l’élevage · ${
          siteReadAt === null ? 'ses chiens, ses futures portées' : this.buildSiteReadLabel(siteReadAt, now)
        }`,
        href: detail.chiens_de_france_site_url,
      })
    }
    if (detail.website !== null && detail.website !== detail.chiens_de_france_site_url) {
      links.push({
        key: 'website',
        logo: this.pickLinkLogo(detail.website),
        label: 'Site de l’élevage',
        description: this.buildReadableAddress(detail.website),
        href: detail.website,
      })
    }
    const origins: Record<string, SocialLinkOrigin> = detail.social_link_origins ?? {}
    if (detail.facebook_url !== null) {
      links.push({
        key: 'facebook',
        logo: 'facebook',
        label: SOCIAL_ACCOUNT_LABELS.facebook,
        description: this.joinOrigin('Page de l’élevage', origins['facebook']),
        href: detail.facebook_url,
      })
    }
    if (detail.instagram_url !== null) {
      links.push({
        key: 'instagram',
        logo: 'instagram',
        label: SOCIAL_ACCOUNT_LABELS.instagram,
        description: this.joinOrigin('Compte de l’élevage', origins['instagram']),
        href: detail.instagram_url,
      })
    }
    if (detail.youtube_url !== null) {
      links.push({
        key: 'youtube',
        logo: 'youtube',
        label: SOCIAL_ACCOUNT_LABELS.youtube,
        description: this.joinOrigin('Chaîne de l’élevage', origins['youtube']),
        href: detail.youtube_url,
      })
    }
    detail.links.forEach((link: BreederLink, index: number): void => {
      links.push({
        key: `link-${index}`,
        logo: this.pickLinkLogo(link.url),
        label: `${link.label} · ajouté par toi`,
        description: this.buildReadableAddress(link.url),
        href: link.url,
      })
    })
    return links
  }

  /**
   * Word the reminder of a follow.
   *
   * @param follow - The follow.
   * @returns « Rappel · le 8 nov. à 9 h », or null without a reminder.
   */
  static buildReminderLabel(follow: BreederFollow): string | null {
    if (!follow.next_reminder_at) {
      return null
    }
    return `Rappel · ${FrenchDate.formatDayAndTime(FrenchDate.parseApiDate(follow.next_reminder_at))}`
  }

  /**
   * Pick where the primary button leads: the phone when known, else the site of the breeding.
   *
   * @param detail - The breeder.
   * @returns The link and its label, or null when nothing is known.
   */
  static resolvePrimaryAction(detail: BreederDetail): PrimaryAction | null {
    if (detail.phone_e164 !== null) {
      return { href: `tel:${detail.phone_e164}`, label: 'Appeler l’éleveur', isCall: true }
    }
    const site: string | null = detail.chiens_de_france_site_url ?? detail.website
    if (site !== null) {
      return { href: site, label: 'Voir le site de l’élevage', isCall: false }
    }
    return null
  }

  /**
   * Word the role of a dog of the breeding.
   *
   * @param dog - The dog.
   * @returns « Chienne », « Étalon » or « Reproducteur ».
   */
  static buildDogRoleLabel(dog: BreederDog): string {
    if (dog.sex === 'female') {
      return 'Chienne'
    }
    if (dog.sex === 'male') {
      return 'Étalon'
    }
    return 'Reproducteur'
  }

  /**
   * Name a dog as its card shows it.
   *
   * @param dog - The dog.
   * @returns The full name, else the name, else « Chien ».
   */
  static buildDogName(dog: BreederDog): string {
    return dog.full_name ?? dog.name ?? 'Chien'
  }

  /**
   * Build the facts line of a dog: its colour, what it carries of the gold, then its other health tests.
   *
   * @param dog - The dog.
   * @returns « Gold · testé gold (e/e) · FN-1.1 · PRCD-1.1 », or null when nothing is known.
   */
  static buildDogFactsLine(dog: BreederDog): string | null {
    const parts: string[] = []
    if (dog.color !== 'inconnue') {
      parts.push(COAT_COLOR_LABELS[dog.color])
    }
    const genotypeLabel: string | null = GoldGeneticsPresentation.buildGenotypeLabel(dog, this.resolveDogGender(dog))
    if (genotypeLabel !== null) {
      parts.push(genotypeLabel)
    }
    parts.push(
      ...dog.health_codes
        .filter((code: string): boolean => genotypeLabel === null || !E_LOCUS_CODE_PATTERN.test(code))
        .map((code: string): string => code.replaceAll('-', `-${WORD_JOINER}`)),
    )
    return parts.length === 0 ? null : parts.join(`${NO_BREAK_SPACE}· `)
  }

  /**
   * Name the Centrale Canine rating of a dog, agreed with its sex.
   *
   * @param dog - The dog.
   * @returns « Confirmée » for a female rated 1, or null when it has no rating.
   */
  static buildDogRatingLabel(dog: BreederDog): string | null {
    if (dog.rating === null) {
      return null
    }
    return LitterDetailPresentation.buildParentRatingLabel(dog.rating, dog.sex === 'female' ? 'dam' : 'sire')
  }

  /**
   * Pick the dogs shown before « les autres chiens »: the parents of its current litters, then the next ones.
   *
   * @param detail - The breeder.
   * @returns The dogs shown.
   */
  static listShownDogs(detail: BreederDetail): BreederDog[] {
    const currentParentsCount: number = detail.reproducers.filter(
      (dog: BreederDog): boolean => dog.is_current_litter_parent,
    ).length
    return detail.reproducers.slice(0, Math.max(BREEDER_DOGS_SHOWN_COUNT, currentParentsCount))
  }

  /**
   * Word the row that leads to the dogs not shown.
   *
   * @param hiddenDogsCount - Dogs not shown.
   * @param isOnSite - Whether the row opens the breeder's site.
   * @returns « 34 autres chiens sur son site », or « 2 autres chiens » when they open on the page.
   */
  static buildHiddenDogsLabel(hiddenDogsCount: number, isOnSite: boolean): string {
    const dogsLabel: string = `${hiddenDogsCount} ${FrenchText.pickForm(hiddenDogsCount, 'autre chien', 'autres chiens')}`
    return isOnSite ? `${dogsLabel} sur son site` : dogsLabel
  }

  /**
   * Build the row that opens the litters born at the breeder, on its site: those of the last year it shows.
   *
   * @param detail - The breeder.
   * @returns « Ses 7 portées de 2026, en photos sur son site » and its link, or null without them.
   */
  static buildSiteLittersLink(detail: BreederDetail): BreederSiteLink | null {
    const siteLittersYear: BreederSiteLittersYear | null = this.countSiteLittersOfLatestYear(detail)
    const href: string | null = detail.site_litters_url ?? null
    if (siteLittersYear === null || href === null) {
      return null
    }
    const littersLabel: string =
      siteLittersYear.littersCount === 1
        ? `Sa portée de ${siteLittersYear.year}`
        : `Ses ${siteLittersYear.littersCount} portées de ${siteLittersYear.year}`
    return { label: `${littersLabel}, en photos sur son site`, href }
  }

  /**
   * Say what a pasted link is, and what becomes of it, before it is added.
   *
   * @param preview - What the API recognised.
   * @param breeder - The breeder it is pasted on.
   * @returns « Son site Chiens de France » and what will be read; for another site, the accounts its page links.
   */
  static buildLinkRecognition(preview: BreederLinkPreview, breeder: BreederDetail): BreederLinkRecognition {
    if (preview.kind === 'chiens_de_france_site') {
      return {
        title: 'Son site Chiens de France',
        helper: 'Ses chiens, ses chiots et ses futures portées seront lus tout de suite, puis chaque matin.',
        accountLabels: [],
      }
    }
    if (preview.kind === 'website') {
      return this.buildWebsiteRecognition(preview, breeder)
    }
    const recognition: BreederSocialAccountRecognition = SOCIAL_ACCOUNT_RECOGNITIONS[preview.kind]
    const knownAddress: string | null = this.readSocialAddress(breeder, preview.kind)
    let helper: string = recognition.helperWhenReplacing
    if (knownAddress === null) {
      helper = recognition.helperWhenNew
    } else if (knownAddress === preview.address) {
      helper = recognition.helperWhenKnown
    }
    return { title: recognition.title, helper, accountLabels: [] }
  }

  /**
   * Say what another site gives: the accounts at the bottom of its page, and which ones « Vu sur » lacks.
   *
   * @param preview - What the API recognised.
   * @param breeder - The breeder it is pasted on.
   * @returns « Le site de l’élevage » and its accounts, or « Une autre page » when its page could not be read.
   */
  private static buildWebsiteRecognition(preview: BreederLinkPreview, breeder: BreederDetail): BreederLinkRecognition {
    if (!preview.is_page_read) {
      return { title: 'Une autre page', helper: 'Elle ira dans « Vu sur ».', accountLabels: [] }
    }
    const accounts: BreederSocialAccountKind[] = preview.social_accounts
      .map((socialAccount: BreederSocialAccount): string => socialAccount.account)
      .filter((account: string): account is BreederSocialAccountKind => Object.hasOwn(SOCIAL_ACCOUNT_LABELS, account))
    if (accounts.length === 0) {
      return { title: 'Le site de l’élevage', helper: 'Il ira dans « Vu sur ».', accountLabels: [] }
    }
    const accountsCount: number = accounts.length
    const missingAccountsCount: number = accounts.filter(
      (account: BreederSocialAccountKind): boolean => this.readSocialAddress(breeder, account) === null,
    ).length
    let fate: string = 'Ceux qui manquent iront dans « Vu sur ».'
    if (missingAccountsCount === accountsCount) {
      fate = FrenchText.pickForm(accountsCount, 'Il ira dans « Vu sur ».', 'Ils iront dans « Vu sur ».')
    } else if (missingAccountsCount === 0) {
      fate = FrenchText.pickForm(accountsCount, 'Il est déjà dans « Vu sur ».', 'Ils sont déjà dans « Vu sur ».')
    }
    const accountsWord: string = FrenchText.spellOutCount(accountsCount, 'masculine').toLowerCase()
    return {
      title: 'Le site de l’élevage',
      helper: `En bas de sa page, ${accountsWord} ${FrenchText.pickForm(accountsCount, 'compte', 'comptes')}. ${fate}`,
      accountLabels: accounts.map((account: BreederSocialAccountKind): string => SOCIAL_ACCOUNT_LABELS[account]),
    }
  }

  /**
   * Read the address of a social account the breeder already has.
   *
   * @param breeder - The breeder.
   * @param account - Facebook, Instagram or YouTube.
   * @returns The address, or null when « Vu sur » has none.
   */
  private static readSocialAddress(breeder: BreederDetail, account: BreederSocialAccountKind): string | null {
    const addresses: Record<BreederSocialAccountKind, string | null> = {
      facebook: breeder.facebook_url,
      instagram: breeder.instagram_url,
      youtube: breeder.youtube_url,
    }
    return addresses[account]
  }

  /**
   * Count the litters the breeder's site shows for the last year it has some.
   *
   * @param detail - The breeder.
   * @returns The year and its litters, or null while the site shows none.
   */
  private static countSiteLittersOfLatestYear(detail: BreederDetail): BreederSiteLittersYear | null {
    const birthYears: number[] = (detail.site_litters ?? []).map((litter: BreederSiteLitter): number =>
      FrenchDate.parseDay(litter.birth_date).getFullYear(),
    )
    if (birthYears.length === 0) {
      return null
    }
    const latestYear: number = Math.max(...birthYears)
    return {
      year: latestYear,
      littersCount: birthYears.filter((year: number): boolean => year === latestYear).length,
    }
  }

  /**
   * Say when the breeder's site was last read.
   *
   * @param siteReadAt - The reading, API date-time.
   * @param now - Current time.
   * @returns « relu ce matin », « relu aujourd’hui », « relu hier » or « relu le 28 oct. ».
   */
  private static buildSiteReadLabel(siteReadAt: string, now: Date): string {
    return `relu ${FrenchDate.formatRecentMoment(FrenchDate.parseApiDate(siteReadAt), now)}`
  }

  /**
   * Add to the description of a social account where its link comes from.
   *
   * @param description - « Page de l’élevage ».
   * @param origin - Where the link comes from, unknown for an account known before the origins were kept.
   * @returns « Page de l’élevage · lien pris sur son site ».
   */
  private static joinOrigin(description: string, origin: SocialLinkOrigin | undefined): string {
    return origin === undefined ? description : `${description} · ${SOCIAL_LINK_ORIGIN_LABELS[origin]}`
  }

  /**
   * Write a web address as « Vu sur » shows it, without its scheme, its « www. » nor its last slash.
   *
   * @param url - The address.
   * @returns « elevage-de-test.fr/cockers » for « https://www.elevage-de-test.fr/cockers/ ».
   */
  private static buildReadableAddress(url: string): string {
    return url.replace(ADDRESS_SCHEME_AND_WWW, '').replace(ADDRESS_LAST_SLASH, '')
  }

  /**
   * Pick the logo of a link by the site it leads to.
   *
   * @param url - The link; a subdomain counts as its site, so `fonddelachenaie.chiens-de-france.com` is Chiens de France.
   * @returns The logo of the site, or the globe of an unknown website.
   */
  private static pickLinkLogo(url: string): LinkLogo {
    let host: string = ''
    try {
      host = new URL(url).hostname.toLowerCase()
    } catch {
      return 'website'
    }
    const knownSite: [string, LinkLogoImage] | undefined = LINK_LOGOS_BY_DOMAIN.find(
      ([domain]: [string, LinkLogoImage]): boolean => host === domain || host.endsWith(`.${domain}`),
    )
    return knownSite?.[1] ?? 'website'
  }

  /**
   * The grammatical gender French gives a dog: feminine for a female.
   *
   * @param dog - The dog.
   * @returns Its gender, masculine when its sex is unknown.
   */
  private static resolveDogGender(dog: BreederDog): FrenchGender {
    return dog.sex === 'female' ? 'feminine' : 'masculine'
  }

  /**
   * Word the line of a current litter: when it is born or due, then its colour and its puppies.
   *
   * @param litter - The litter.
   * @param now - Current time.
   * @returns The line, hot when it calls for a call.
   */
  private static buildCurrentLitterLine(litter: LitterCard, now: Date): BreederLitterStatusLine {
    const parts: string[] = []
    const isBornLastNight: boolean = LitterPresentation.isBornLastNight(litter, now)
    parts.push(
      isBornLastNight ? 'Née cette nuit' : (LitterPresentation.buildBirthFact(litter, now) ?? 'Portée en cours'),
    )
    const details: string[] = []
    if (LitterPresentation.hasKnownColors(litter.colors)) {
      details.push(LitterPresentation.buildColorLabel(litter.colors, true).toLowerCase())
    }
    if (LitterPresentation.arePuppiesAvailableWorthTelling(litter)) {
      const puppiesAvailable: string | null = LitterPresentation.buildPuppiesAvailableLabel(litter)
      if (puppiesAvailable !== null) {
        details.push(puppiesAvailable.toLowerCase())
      }
    } else {
      const sexCounts: string[] = LitterPresentation.listSexCounts(litter)
      if (sexCounts.length > 0) {
        details.push(sexCounts.join(' et '))
      }
    }
    if (details.length > 0) {
      parts.push(details.join(', '))
    }
    const isRecentBirth: boolean =
      litter.birth_date !== null &&
      FrenchDate.countDaysAgo(FrenchDate.parseDay(litter.birth_date), now) <= HOT_BIRTH_AGE_DAYS
    const isBirthStillToCome: boolean =
      litter.kind === 'litter_expected' && !FollowUpPresentation.isBirthOverdue(litter, now)
    return { text: parts.join(' · '), tone: isBirthStillToCome || isRecentBirth ? 'hot' : 'normal' }
  }
}
