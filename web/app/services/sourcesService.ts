import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  ListingSource,
  SourceActivity,
  SourceStatus,
} from '~/types/api'
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
   * Fetch what runs now: the sources the server reads, and where the relay of the desktop app stands.
   *
   * @returns The activity.
   */
  static async readActivity(): Promise<SourceActivity> {
    return ApiClient.get<SourceActivity>('/api/v1/sources/activity')
  }

  /**
   * Run a collection now: the API answers at once, the run goes on in the background.
   *
   * @param source - The source.
   * @returns What runs now, the source included.
   */
  static async run(source: ListingSource): Promise<SourceActivity> {
    return ApiClient.post<SourceActivity>(`/api/v1/sources/${source}/run`, {})
  }

  /**
   * Relay the Centrale Canine from the desktop app: send the pages read, get what to do next.
   *
   * @param relayRequest - The relay token and the pages read since the previous call.
   * @returns What the desktop app does next.
   */
  static async relayCentraleCanine(relayRequest: CentraleCanineRelayRequest): Promise<CentraleCanineRelayAnswer> {
    return ApiClient.post<CentraleCanineRelayAnswer>('/api/v1/sources/centrale_canine/relay', relayRequest)
  }

  /**
   * Ask the desktop app of a computer that is on to relay the Centrale Canine at its next check, within a minute.
   *
   * @returns What runs now, the request waiting included.
   */
  static async requestCentraleCanineRelay(): Promise<SourceActivity> {
    return ApiClient.post<SourceActivity>('/api/v1/sources/centrale_canine/relay-request', {})
  }
}
