import type { LitterCard } from '~/types/api'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

/** How a shared litter reads: in the share drawer, and on the page the link opens without an account. */
export class LitterSharePresentation {
  /**
   * Build the line under the name in the share drawer.
   *
   * @param litter - The litter.
   * @returns « Née le 27 oct. · gold · 2 mâles, 3 femelles », the unknown parts left out.
   */
  static buildSummaryLine(litter: LitterCard): string {
    const parts: string[] = []
    const birthFact: string | null = LitterPresentation.buildBirthFact(litter)
    if (birthFact !== null) {
      parts.push(birthFact)
    }
    if (LitterPresentation.hasKnownColors(litter.colors)) {
      parts.push(LitterPresentation.buildColorPhrase(litter.colors))
    }
    const sexCounts: string[] = LitterPresentation.listSexCounts(litter)
    if (sexCounts.length > 0) {
      parts.push(sexCounts.join(', '))
    }
    return parts.join(' · ')
  }

  /**
   * Build the title of the shared page.
   *
   * @param sharerName - First name of who shared the litter.
   * @returns « Léo t’a partagé une portée ».
   */
  static buildTitle(sharerName: string): string {
    const name: string = sharerName.trim()
    return name === '' ? 'On t’a partagé une portée' : `${name} t’a partagé une portée`
  }

  /**
   * Build the birth line above the name on the shared page.
   *
   * @param litter - The litter.
   * @returns « NÉE LE 27 OCT. », « À NAÎTRE VERS LE 7 NOV. », or null while the birth is unknown.
   */
  static buildBirthLabel(litter: LitterCard): string | null {
    return LitterPresentation.buildBirthFact(litter)?.toUpperCase() ?? null
  }

  /**
   * Build the footer of the shared page.
   *
   * @param expiresAt - Expiry of the link, from the API.
   * @returns « Lien privé, valable jusqu’au 30 nov. ».
   */
  static buildExpiryLine(expiresAt: string): string {
    return `Lien privé, valable jusqu’au ${FrenchDate.formatDayAndShortMonth(FrenchDate.parseApiDate(expiresAt))}`
  }
}
