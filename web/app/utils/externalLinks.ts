const WEB_PROTOCOLS: string[] = ['http:', 'https:']

/** Links of the desktop app that lead to another site, opened in the default browser. */
export class ExternalLinks {
  /**
   * Find the address a clicked link opens in the default browser.
   *
   * @param linkHref - The address of the link, as the page resolved it.
   * @param appOrigin - The origin of the pages of the app.
   * @returns The address on another site, or null for a page of the app, a phone number or anything but the web.
   */
  static findUrlToOpenInBrowser(linkHref: string, appOrigin: string): string | null {
    let linkUrl: URL
    try {
      linkUrl = new URL(linkHref)
    } catch {
      return null
    }
    if (!WEB_PROTOCOLS.includes(linkUrl.protocol) || linkUrl.origin === appOrigin) {
      return null
    }
    return linkUrl.href
  }
}
