import type { MapAppKey, MapAppLink, MapDestination } from '~/types/Location'

const MAP_APP_LABELS: Record<MapAppKey, string> = {
  apple_maps: 'Apple Plans',
  google_maps: 'Google Maps',
  waze: 'Waze',
}

const MAP_APP_KEYS: MapAppKey[] = ['apple_maps', 'google_maps', 'waze']

/** Links that open the route to a breeding in the map apps of the phone: the app itself when it is installed. */
export class MapLinks {
  /**
   * Build one link per map app towards a destination.
   *
   * @param destination - The breeding, by its position when known, else by its place name.
   * @returns The links, Apple Plans first.
   */
  static buildDirectionsLinks(destination: MapDestination): MapAppLink[] {
    return MAP_APP_KEYS.map((key: MapAppKey): MapAppLink => ({
      key,
      label: MAP_APP_LABELS[key],
      href: this.buildDirectionsHref(key, destination),
    }))
  }

  /**
   * Build the universal link of one map app.
   *
   * @param key - The map app.
   * @param destination - The breeding.
   * @returns The link, ready for a tap.
   */
  private static buildDirectionsHref(key: MapAppKey, destination: MapDestination): string {
    const target: string = destination.point
      ? `${destination.point.latitude},${destination.point.longitude}`
      : destination.placeName
    const encodedTarget: string = encodeURIComponent(target)
    switch (key) {
      case 'apple_maps':
        return `https://maps.apple.com/?daddr=${encodedTarget}`
      case 'google_maps':
        return `https://www.google.com/maps/dir/?api=1&destination=${encodedTarget}`
      case 'waze':
        return destination.point
          ? `https://waze.com/ul?ll=${encodedTarget}&navigate=yes`
          : `https://waze.com/ul?q=${encodedTarget}&navigate=yes`
    }
  }
}
