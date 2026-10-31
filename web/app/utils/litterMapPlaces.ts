import type { LitterCard } from '~/types/api'
import type { AnchoredLitterMapCluster, LitterMapCluster, LitterMapPlace, ScreenPoint } from '~/types/LitterMap'
import type { GeographicPoint } from '~/types/Location'
import { CrowFliesDistance } from '~/utils/crowFliesDistance'

const POSITION_DECIMALS: number = 5
const UNKNOWN_SCORE_LABEL: string = '–'

/** Room a pin takes on screen: two pins closer than this would overlap, so they share one pin. */
export const MAP_PIN_BOX_WIDTH_IN_PIXELS: number = 104
export const MAP_PIN_BOX_HEIGHT_IN_PIXELS: number = 44

/** Where the litters sit on the map: one place per breeding address, and the places close on screen gathered. */
export class LitterMapPlaces {
  /**
   * Group the litters that share a position; a litter without one has no place.
   *
   * @param litters - Cards of the home, in their order.
   * @returns The places, in the order their first litter appears.
   */
  static groupByPosition(litters: LitterCard[]): LitterMapPlace[] {
    const places: Map<string, LitterMapPlace> = new Map()
    for (const litter of litters) {
      if (litter.breeder_latitude === null || litter.breeder_longitude === null) {
        continue
      }
      const positionKey: string = `${litter.breeder_latitude.toFixed(POSITION_DECIMALS)},${litter.breeder_longitude.toFixed(POSITION_DECIMALS)}`
      const place: LitterMapPlace | undefined = places.get(positionKey)

      if (place !== undefined) {
        place.litters.push(litter)
        continue
      }
      places.set(positionKey, {
        point: { latitude: litter.breeder_latitude, longitude: litter.breeder_longitude },
        litters: [litter],
      })
    }
    return [...places.values()]
  }

  /**
   * Gather the places whose pins would overlap at the current zoom, around the best ranked one.
   *
   * @param places - Places, the best ranked first.
   * @param project - Position of a point on screen at the current zoom.
   * @returns The clusters, in the order of their first place.
   */
  static cluster(places: LitterMapPlace[], project: (point: GeographicPoint) => ScreenPoint): LitterMapCluster[] {
    const anchoredClusters: AnchoredLitterMapCluster[] = []
    for (const place of places) {
      const position: ScreenPoint = project(place.point)
      const owner: AnchoredLitterMapCluster | undefined = anchoredClusters.find(
        (anchoredCluster: AnchoredLitterMapCluster): boolean =>
          Math.abs(anchoredCluster.anchor.x - position.x) < MAP_PIN_BOX_WIDTH_IN_PIXELS &&
          Math.abs(anchoredCluster.anchor.y - position.y) < MAP_PIN_BOX_HEIGHT_IN_PIXELS,
      )

      if (owner !== undefined) {
        owner.cluster.places.push(place)
        owner.cluster.litters.push(...place.litters)
        continue
      }
      anchoredClusters.push({
        anchor: position,
        cluster: { point: place.point, places: [place], litters: [...place.litters] },
      })
    }
    return anchoredClusters.map(
      (anchoredCluster: AnchoredLitterMapCluster): LitterMapCluster => anchoredCluster.cluster,
    )
  }

  /**
   * The points the map opens on: the home and its closest places, or every place while the home is unknown.
   *
   * @param places - The places.
   * @param home - Position of the device, null while unknown.
   * @param closestPlaceCount - How many places to show around the home.
   * @returns The points to fit the map on.
   */
  static pointsToOpenOn(
    places: LitterMapPlace[],
    home: GeographicPoint | null,
    closestPlaceCount: number,
  ): GeographicPoint[] {
    const placePoints: GeographicPoint[] = places.map((place: LitterMapPlace): GeographicPoint => place.point)

    if (home === null) {
      return placePoints
    }
    const closestPoints: GeographicPoint[] = [...placePoints]
      .sort(
        (first: GeographicPoint, second: GeographicPoint): number =>
          CrowFliesDistance.kilometersBetween(home, first) - CrowFliesDistance.kilometersBetween(home, second),
      )
      .slice(0, closestPlaceCount)
    return [home, ...closestPoints]
  }

  /**
   * What a pin says, for its accessible name: the litter and its score, or how many litters it gathers.
   *
   * @param litters - Litters of the pin.
   * @returns « Des Bords de Vilaine, 96 % » or « 3 portées ».
   */
  static buildPinLabel(litters: LitterCard[]): string {
    const firstLitter: LitterCard | undefined = litters[0]

    if (litters.length > 1 || firstLitter === undefined) {
      return `${litters.length} portées`
    }
    return `${firstLitter.name}, ${this.buildScoreLabel(firstLitter)}`
  }

  /**
   * The score of a litter as its pin shows it.
   *
   * @param litter - The litter.
   * @returns « 88 % », or a dash while the score is unknown.
   */
  static buildScoreLabel(litter: LitterCard): string {
    return litter.score === null ? UNKNOWN_SCORE_LABEL : `${litter.score} %`
  }
}
