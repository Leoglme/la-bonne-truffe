import type {
  BreederCard,
  BreederColorShare,
  BreederDetail,
  BreederDog,
  BreederFilter,
  BreederFollow,
  BreederLink,
  LitterCard,
} from '~/types/api'
import type {
  BreederChip,
  BreederColorShareSlice,
  BreederLitterStatusLine,
  BreederSeenOnLink,
  BreederStat,
} from '~/types/Breeder'
import type { DevicePosition } from '~/types/Location'
import type { PrimaryAction } from '~/types/PrimaryAction'
import { COAT_COLOR_SWATCHES } from '~/constants/breederOptions'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { UNKNOWN_PLACE_LABEL } from '~/constants/litterLabels'
import { CrowFliesDistance } from '~/utils/crowFliesDistance'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'
import { LitterPresentation } from '~/utils/litterPresentation'

const INITIALS_SKIPPED_WORDS: Set<string> = new Set(['de', 'des', 'du', 'd', 'la', 'le', 'les', 'l', 'et', 'au', 'aux'])
const HOT_BIRTH_AGE_DAYS: number = 7
const INACTIVE_AFTER_DAYS: number = 2 * 365
const SIREN_DIGIT_GROUP: RegExp = /(\d{3})(?=\d)/g
const MONTH_AND_YEAR_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' })
const MONTH_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat('fr-FR', { month: 'long' })

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
   * Build the three figures of the breeder page.
   *
   * @param detail - The breeder.
   * @returns Gold litters, last litter, rhythm.
   */
  static buildStats(detail: BreederDetail): BreederStat[] {
    const lastLitter: string = detail.last_litter_date
      ? FrenchDate.formatDayAndShortMonth(FrenchDate.parseDay(detail.last_litter_date))
      : '—'
    const rhythmParts: string[] = []
    if (detail.litters_last_year_count !== null) {
      rhythmParts.push(`${detail.litters_last_year_count} par an`)
    }
    if (detail.breeding_females_count !== null) {
      rhythmParts.push(
        `${detail.breeding_females_count} ${FrenchText.pickForm(detail.breeding_females_count, 'lice', 'lices')}`,
      )
    }
    return [
      {
        label: 'Portées gold',
        compactLabel: 'Gold',
        value: detail.litters_count === 0 ? '—' : `${detail.gold_litters_count} sur ${detail.litters_count}`,
      },
      { label: 'Dernière portée', compactLabel: 'Dernière', value: lastLitter },
      { label: 'Rythme', compactLabel: 'Rythme', value: rhythmParts.length === 0 ? '—' : rhythmParts.join(' · ') },
    ]
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
   * @returns The rows, the directories first, then the sites and the social accounts, then what was added by hand.
   */
  static listSeenOnLinks(detail: BreederDetail): BreederSeenOnLink[] {
    const links: BreederSeenOnLink[] = []
    if (detail.scc_breeder_id !== null) {
      const facts: string[] = [detail.affix ? 'Affixe déposé' : 'Éleveur déclaré']
      if (detail.siren) {
        facts.push(`SIREN ${detail.siren.replace(SIREN_DIGIT_GROUP, '$1 ')}`)
      }
      links.push({ key: 'scc', label: 'Centrale Canine', description: facts.join(' · '), href: null })
    }
    if (detail.chiens_de_france_site_url !== null) {
      links.push({
        key: 'chiens-de-france',
        label: 'Chiens de France',
        description: 'Site de l’élevage · ses chiens, ses futures portées',
        href: detail.chiens_de_france_site_url,
      })
    }
    if (detail.website !== null && detail.website !== detail.chiens_de_france_site_url) {
      links.push({ key: 'website', label: 'Site de l’élevage', description: detail.website, href: detail.website })
    }
    if (detail.facebook_url !== null) {
      links.push({ key: 'facebook', label: 'Facebook', description: 'Page de l’élevage', href: detail.facebook_url })
    }
    if (detail.instagram_url !== null) {
      links.push({
        key: 'instagram',
        label: 'Instagram',
        description: 'Compte de l’élevage',
        href: detail.instagram_url,
      })
    }
    if (detail.youtube_url !== null) {
      links.push({ key: 'youtube', label: 'YouTube', description: 'Chaîne de l’élevage', href: detail.youtube_url })
    }
    detail.links.forEach((link: BreederLink, index: number): void => {
      links.push({
        key: `link-${index}`,
        label: `${link.label} · ajouté par toi`,
        description: link.url,
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
   * @returns « Lice », « Étalon » or « Reproducteur ».
   */
  static buildDogRoleLabel(dog: BreederDog): string {
    if (dog.sex === 'female') {
      return 'Lice'
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
   * Build the facts line of a dog: its colour, then its health tests.
   *
   * @param dog - The dog.
   * @returns « Gold · FN-1.1 · PRCD-1.1 », or null when nothing is known.
   */
  static buildDogFactsLine(dog: BreederDog): string | null {
    const parts: string[] = []
    if (dog.color !== 'inconnue') {
      parts.push(COAT_COLOR_LABELS[dog.color])
    }
    parts.push(...dog.health_codes)
    return parts.length === 0 ? null : parts.join(' · ')
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
    parts.push(isBornLastNight ? 'Née cette nuit' : (LitterPresentation.buildBirthFact(litter) ?? 'Portée en cours'))
    const details: string[] = []
    if (LitterPresentation.hasKnownColors(litter.colors)) {
      details.push(LitterPresentation.buildColorLabel(litter.colors, true).toLowerCase())
    }
    if (LitterPresentation.arePuppiesAvailableWorthTelling(litter)) {
      const puppiesAvailable: string | null = LitterPresentation.buildPuppiesAvailableLabel(litter)
      if (puppiesAvailable !== null) {
        details.push(puppiesAvailable.toLowerCase())
      }
    } else if (LitterPresentation.hasKnownSexes(litter)) {
      details.push(LitterPresentation.listSexCounts(litter).join(' et '))
    }
    if (details.length > 0) {
      parts.push(details.join(', '))
    }
    const isRecentBirth: boolean =
      litter.birth_date !== null &&
      FrenchDate.countDaysAgo(FrenchDate.parseDay(litter.birth_date), now) <= HOT_BIRTH_AGE_DAYS
    return { text: parts.join(' · '), tone: litter.kind === 'litter_expected' || isRecentBirth ? 'hot' : 'normal' }
  }
}
