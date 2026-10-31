import type { FeatureCollection } from 'geojson'
import departmentOutlinesUrl from '~/assets/geo/departments.json?url'

/** Reads the outlines of the departments the map is drawn with, a file built into the app. */
export class DepartmentOutlinesService {
  /**
   * Load the outlines.
   *
   * @returns The outlines, or null when they cannot be read.
   */
  static async load(): Promise<FeatureCollection | null> {
    try {
      const response: Response = await fetch(departmentOutlinesUrl)
      const outlines: unknown = await response.json()
      return this.isFeatureCollection(outlines) ? outlines : null
    } catch {
      return null
    }
  }

  /**
   * Whether a parsed file is a GeoJSON feature collection.
   *
   * @param value - The parsed file.
   * @returns True for a feature collection.
   */
  private static isFeatureCollection(value: unknown): value is FeatureCollection {
    return typeof value === 'object' && value !== null && 'type' in value && value.type === 'FeatureCollection'
  }
}
