import type { MapApp, MapAppKey } from '~/types/Location'

/** The map apps of the phone: their name, and their logo from the Simple Icons set in the colour of the brand. */
export const MAP_APPS: Record<MapAppKey, MapApp> = {
  apple_maps: { label: 'Apple Plans', iconName: 'i-simple-icons-apple', colorClass: 'text-brand-apple' },
  google_maps: { label: 'Google Maps', iconName: 'i-simple-icons-googlemaps', colorClass: 'text-brand-google' },
  waze: { label: 'Waze', iconName: 'i-simple-icons-waze', colorClass: 'text-brand-waze' },
}
