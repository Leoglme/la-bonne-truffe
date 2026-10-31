import type { GeographicPoint } from '~/types/Location'

const OSRM_TABLE_URL: string = 'https://router.project-osrm.org/table/v1/driving'
const SECONDS_PER_MINUTE: number = 60

/** Asks the public OSRM router, fed by OpenStreetMap, how long the drives from one point take. */
export class DrivingTimeService {
  /**
   * Ask, in a single request, how many minutes the drive takes from a point to each destination.
   *
   * @param from - Where the drives start.
   * @param destinations - Where they end.
   * @returns The minutes per destination, in their order, null where the router gives none.
   */
  static async fetchMinutes(from: GeographicPoint, destinations: GeographicPoint[]): Promise<(number | null)[]> {
    const unanswered: (number | null)[] = destinations.map((): null => null)

    if (destinations.length === 0) {
      return unanswered
    }
    const coordinates: string = [from, ...destinations]
      .map((point: GeographicPoint): string => `${point.longitude},${point.latitude}`)
      .join(';')
    try {
      const response: Response = await fetch(`${OSRM_TABLE_URL}/${coordinates}?sources=0&annotations=duration`)

      if (!response.ok) {
        return unanswered
      }
      const secondsFromStart: unknown[] | null = this.readFirstRow(await response.json())

      if (secondsFromStart === null) {
        return unanswered
      }
      return secondsFromStart
        .slice(1, destinations.length + 1)
        .map((seconds: unknown): number | null =>
          typeof seconds === 'number' ? Math.max(1, Math.round(seconds / SECONDS_PER_MINUTE)) : null,
        )
    } catch {
      return unanswered
    }
  }

  /**
   * Read the durations from the starting point in an answer of the OSRM table service.
   *
   * @param body - The parsed answer.
   * @returns Its first row of seconds, the starting point first, or null when the answer has none.
   */
  private static readFirstRow(body: unknown): unknown[] | null {
    if (typeof body !== 'object' || body === null || !('durations' in body) || !Array.isArray(body.durations)) {
      return null
    }
    const firstRow: unknown = body.durations[0]
    return Array.isArray(firstRow) ? firstRow : null
  }
}
