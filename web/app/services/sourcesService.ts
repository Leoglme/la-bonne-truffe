import type { CentraleCanineRelayAnswer, CentraleCanineRelayRequest, ListingSource, SourceStatus } from '~/types/api'
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

  /**
   * Relay the Centrale Canine from the desktop app: send the pages read, get what to do next.
   *
   * @param relayRequest - The relay token and every page read since the relay started.
   * @returns What the desktop app does next.
   */
  static async relayCentraleCanine(relayRequest: CentraleCanineRelayRequest): Promise<CentraleCanineRelayAnswer> {
    return ApiClient.post<CentraleCanineRelayAnswer>('/api/v1/sources/centrale_canine/relay', relayRequest)
  }

  /**
   * Ask the desktop app of a computer that is on to relay the Centrale Canine at its next check.
   */
  static async requestCentraleCanineRelay(): Promise<void> {
    await ApiClient.post('/api/v1/sources/centrale_canine/relay-request', {})
  }
}
