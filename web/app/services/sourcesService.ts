import type { ListingSource, SourceStatus } from '~/types/api'
import { ApiClient } from './api'

/** HTTP client for the /sources API resource. */
export class SourcesService {
  /**
   * Fetch the last run of every source.
   *
   * @returns The statuses.
   */
  static async list(): Promise<SourceStatus[]> {
    return ApiClient.get<SourceStatus[]>('/api/v1/sources')
  }

  /**
   * Run a collection now (blocking on the API side).
   *
   * @param source - The source.
   * @returns The statuses after the run.
   */
  static async run(source: ListingSource): Promise<SourceStatus[]> {
    return ApiClient.post<SourceStatus[]>(`/api/v1/sources/${source}/run`, {})
  }
}
