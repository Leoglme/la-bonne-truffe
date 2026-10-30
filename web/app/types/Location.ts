export type GeographicPoint = {
  latitude: number
  longitude: number
}

export type DevicePosition = GeographicPoint & {
  recordedAt: string
}

export type DeviceLocationPermission = 'unknown' | 'granted' | 'denied' | 'unavailable'

export type MapAppKey = 'apple_maps' | 'google_maps' | 'waze'

export type MapAppLink = {
  key: MapAppKey
  label: string
  href: string
}

export type MapDestination = {
  point: GeographicPoint | null
  placeName: string
}
