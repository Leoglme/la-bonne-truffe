import type { Ref } from 'vue'
import type { GeographicPoint } from '~/types/Location'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { DrivingTimeService } from '~/services/drivingTimeService'
import { LitterMapPlaces } from '~/utils/litterMapPlaces'

const HOME_DECIMALS: number = 3

/** Pinia store of the drive times from home to the breedings. */
export const useDrivingTimesStore = defineStore('drivingTimes', () => {
  const minutesByRoute: Ref<Record<string, number>> = ref({})
  const requestedRouteKeys: Set<string> = new Set()

  /**
   * Round the home before it leaves the device: about a hundred metres is enough for a drive time.
   *
   * @param home - Position of the device.
   * @returns The rounded position.
   */
  function roundHome(home: GeographicPoint): GeographicPoint {
    return {
      latitude: Number(home.latitude.toFixed(HOME_DECIMALS)),
      longitude: Number(home.longitude.toFixed(HOME_DECIMALS)),
    }
  }

  /**
   * Build the key of a drive from the rounded home to a breeding.
   *
   * @param home - Position of the device.
   * @param breeding - Position of the breeding.
   * @returns The key of the drive.
   */
  function buildRouteKey(home: GeographicPoint, breeding: GeographicPoint): string {
    return `${LitterMapPlaces.buildPositionKey(home, HOME_DECIMALS)}>${LitterMapPlaces.buildPositionKey(breeding)}`
  }

  /**
   * The drive time from home to a breeding, once the router answered.
   *
   * @param home - Position of the device, null while unknown.
   * @param breeding - Position of the breeding, null while unknown.
   * @returns The minutes, or null.
   */
  function minutesBetween(home: GeographicPoint | null, breeding: GeographicPoint | null): number | null {
    if (home === null || breeding === null) {
      return null
    }
    return minutesByRoute.value[buildRouteKey(home, breeding)] ?? null
  }

  /**
   * Ask the router for the drive times not known yet.
   *
   * @param home - Position of the device.
   * @param breedings - Positions of the breedings.
   */
  async function load(home: GeographicPoint, breedings: GeographicPoint[]): Promise<void> {
    const missingBreedingsByRoute: Map<string, GeographicPoint> = new Map()
    for (const breeding of breedings) {
      const routeKey: string = buildRouteKey(home, breeding)

      if (!requestedRouteKeys.has(routeKey)) {
        missingBreedingsByRoute.set(routeKey, breeding)
      }
    }
    if (missingBreedingsByRoute.size === 0) {
      return
    }
    const routeKeys: string[] = [...missingBreedingsByRoute.keys()]
    for (const routeKey of routeKeys) {
      requestedRouteKeys.add(routeKey)
    }
    const minutes: (number | null)[] = await DrivingTimeService.fetchMinutes(roundHome(home), [
      ...missingBreedingsByRoute.values(),
    ])
    const answeredMinutesByRoute: Record<string, number> = { ...minutesByRoute.value }
    routeKeys.forEach((routeKey: string, routeIndex: number): void => {
      const routeMinutes: number | null = minutes[routeIndex] ?? null

      if (routeMinutes === null) {
        requestedRouteKeys.delete(routeKey)
        return
      }
      answeredMinutesByRoute[routeKey] = routeMinutes
    })
    minutesByRoute.value = answeredMinutesByRoute
  }

  return { minutesByRoute, minutesBetween, load }
})
