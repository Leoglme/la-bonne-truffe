import type { MapAppKey } from '~/types/Location'

export const MAP_APP_LABELS: Record<MapAppKey, string> = {
  apple_maps: 'Apple Plans',
  google_maps: 'Google Maps',
  waze: 'Waze',
}

/** The icon of each app as the App Store shows it (artwork of the store, 128 px, in `public/images/map-apps`). */
export const MAP_APP_ICON_SOURCES: Record<MapAppKey, string> = {
  apple_maps: '/images/map-apps/apple-plans.png',
  google_maps: '/images/map-apps/google-maps.png',
  waze: '/images/map-apps/waze.png',
}
