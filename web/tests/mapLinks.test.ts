import type { MapAppLink } from '../app/types/Location'
import { describe, expect, it } from 'vitest'
import { MapLinks } from '../app/utils/mapLinks'

/**
 * Find the link of one map app.
 *
 * @param links - The links built.
 * @param label - The app, as the sheet names it.
 * @returns Its link.
 */
function hrefOf(links: MapAppLink[], label: string): string {
  const link: MapAppLink | undefined = links.find((candidate: MapAppLink): boolean => candidate.label === label)
  if (link === undefined) {
    throw new Error(`no link for ${label}`)
  }
  return link.href
}

describe('MapLinks', (): void => {
  it('routes to the position of the breeding when it is known', (): void => {
    const links: MapAppLink[] = MapLinks.buildDirectionsLinks({
      point: { latitude: 48.26, longitude: -1.4 },
      placeName: 'Saint-Aubin-du-Cormier, Ille-et-Vilaine',
    })

    expect(links.map((link: MapAppLink): string => link.label)).toEqual(['Apple Plans', 'Google Maps', 'Waze'])
    expect(hrefOf(links, 'Apple Plans')).toBe('https://maps.apple.com/?daddr=48.26%2C-1.4')
    expect(hrefOf(links, 'Google Maps')).toBe('https://www.google.com/maps/dir/?api=1&destination=48.26%2C-1.4')
    expect(hrefOf(links, 'Waze')).toBe('https://waze.com/ul?ll=48.26%2C-1.4&navigate=yes')
  })

  it('routes to the place name when the position is unknown', (): void => {
    const links: MapAppLink[] = MapLinks.buildDirectionsLinks({ point: null, placeName: 'Redon, Ille-et-Vilaine' })

    expect(hrefOf(links, 'Apple Plans')).toBe('https://maps.apple.com/?daddr=Redon%2C%20Ille-et-Vilaine')
    expect(hrefOf(links, 'Google Maps')).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=Redon%2C%20Ille-et-Vilaine',
    )
    expect(hrefOf(links, 'Waze')).toBe('https://waze.com/ul?q=Redon%2C%20Ille-et-Vilaine&navigate=yes')
  })
})
