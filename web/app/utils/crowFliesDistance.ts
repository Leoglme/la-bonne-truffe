import type { GeographicPoint } from '~/types/Location'

const EARTH_RADIUS_KM: number = 6371

/** Distance as the crow flies between two points on Earth, and how it reads on a card. */
export class CrowFliesDistance {
  /**
   * Measure the distance between two points as the crow flies (haversine formula).
   *
   * @param from - Where the person is.
   * @param to - The breeding.
   * @returns The distance in kilometres, not rounded.
   */
  static kilometersBetween(from: GeographicPoint, to: GeographicPoint): number {
    const latitudeDifference: number = this.toRadians(to.latitude - from.latitude)
    const longitudeDifference: number = this.toRadians(to.longitude - from.longitude)
    const halfChordSquared: number =
      Math.sin(latitudeDifference / 2) ** 2 +
      Math.cos(this.toRadians(from.latitude)) *
        Math.cos(this.toRadians(to.latitude)) *
        Math.sin(longitudeDifference / 2) ** 2
    return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(halfChordSquared))
  }

  /**
   * Write a distance as a card shows it.
   *
   * @param kilometers - The distance.
   * @returns « à 32 km », or « à moins d'un kilomètre ».
   */
  static buildLabel(kilometers: number): string {
    const roundedKilometers: number = Math.round(kilometers)
    return roundedKilometers < 1 ? 'à moins d’un kilomètre' : `à ${roundedKilometers} km`
  }

  /**
   * Convert degrees to radians.
   *
   * @param degrees - An angle in degrees.
   * @returns The angle in radians.
   */
  private static toRadians(degrees: number): number {
    return (degrees * Math.PI) / 180
  }
}
