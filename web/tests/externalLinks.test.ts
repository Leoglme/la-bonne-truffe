import { describe, expect, it } from 'vitest'
import { ExternalLinks } from '../app/utils/externalLinks'

const DESKTOP_APP_ORIGIN: string = 'http://tauri.localhost'

describe('ExternalLinks', (): void => {
  it('opens a link to another site in the browser, address unchanged', (): void => {
    expect(
      ExternalLinks.findUrlToOpenInBrowser('https://www.centrale-canine.fr/du-mont-de-la-chenaie', DESKTOP_APP_ORIGIN),
    ).toBe('https://www.centrale-canine.fr/du-mont-de-la-chenaie')
    expect(
      ExternalLinks.findUrlToOpenInBrowser(
        'https://www.google.com/maps/dir/?api=1&destination=48.26%2C-1.4',
        DESKTOP_APP_ORIGIN,
      ),
    ).toBe('https://www.google.com/maps/dir/?api=1&destination=48.26%2C-1.4')
    expect(ExternalLinks.findUrlToOpenInBrowser('http://www.elevage-exemple.fr/', DESKTOP_APP_ORIGIN)).toBe(
      'http://www.elevage-exemple.fr/',
    )
  })

  it('keeps the pages of the app in its window', (): void => {
    expect(ExternalLinks.findUrlToOpenInBrowser('http://tauri.localhost/eleveurs/12', DESKTOP_APP_ORIGIN)).toBeNull()
    expect(ExternalLinks.findUrlToOpenInBrowser('http://localhost:1420/portees/3', 'http://localhost:1420')).toBeNull()
  })

  it('opens the web only, never a program of the computer', (): void => {
    const nonWebHrefs: string[] = [
      'tel:+33612345678',
      'mailto:eleveur@example.fr',
      'file:///C:/Windows/System32/calc.exe',
      'ms-settings:privacy',
      'javascript:alert(1)',
    ]

    for (const nonWebHref of nonWebHrefs) {
      expect(ExternalLinks.findUrlToOpenInBrowser(nonWebHref, DESKTOP_APP_ORIGIN)).toBeNull()
    }
  })

  it('leaves alone an address it cannot read', (): void => {
    expect(ExternalLinks.findUrlToOpenInBrowser('http://[', DESKTOP_APP_ORIGIN)).toBeNull()
  })
})
