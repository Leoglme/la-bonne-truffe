import type { BreederCreate, BreederLink } from '~/types/api'
import type { BreederManualForm } from '~/types/BreederManualForm'

const POSTAL_CODE: RegExp = /\b(\d{5})\b/
const LINK_LABELS_BY_HOST: [string, string][] = [
  ['facebook.com', 'Facebook'],
  ['fb.com', 'Facebook'],
  ['instagram.com', 'Instagram'],
  ['leboncoin.fr', 'Leboncoin'],
  ['tiktok.com', 'TikTok'],
]

/** Turns what was typed on « Ajouter un éleveur » into what the API expects. */
export class BreederManualFormPresentation {
  /**
   * Build the payload of the form: the town and the postal code told apart, the link labelled by its site.
   *
   * @param form - What was typed.
   * @param isFollowed - Whether to follow the breeder at once.
   * @returns The payload, or null without a name.
   */
  static buildPayload(form: BreederManualForm, isFollowed: boolean): BreederCreate | null {
    const displayName: string = form.display_name.trim()
    if (displayName === '') {
      return null
    }
    const postalCode: string | null = POSTAL_CODE.exec(form.place)?.[1] ?? null
    const city: string = form.place
      .replace(POSTAL_CODE, '')
      .replace(/[,\s]+$/, '')
      .replace(/^[,\s]+/, '')
      .trim()
    const link: BreederLink | null = this.buildLink(form.link)
    const note: string = form.note.trim()
    const phone: string = form.phone.trim()
    return {
      display_name: displayName,
      city: city === '' ? null : city,
      zip_code: postalCode,
      phone: phone === '' ? null : phone,
      links: link === null ? [] : [link],
      notes: note === '' ? null : note,
      follow: isFollowed,
    }
  }

  /**
   * Label a link by the site it points at.
   *
   * @param url - The link typed, with or without its scheme.
   * @returns The link, or null when nothing was typed.
   */
  static buildLink(url: string): BreederLink | null {
    const trimmed: string = url.trim()
    if (trimmed === '') {
      return null
    }
    const withScheme: string = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`
    let host: string = ''
    try {
      host = new URL(withScheme).hostname.replace(/^www\./, '')
    } catch {
      return { label: 'Lien', url: trimmed }
    }
    const known: [string, string] | undefined = LINK_LABELS_BY_HOST.find(([knownHost]: [string, string]): boolean =>
      host.endsWith(knownHost),
    )
    return { label: known === undefined ? 'Site' : known[1], url: withScheme }
  }
}
