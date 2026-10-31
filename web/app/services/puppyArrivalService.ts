import type { PuppyArrival, PuppyArrivalChecklist, PuppyArrivalStart } from '~/types/api'
import { ApiClient } from './api'

/** HTTP client for the puppy found: « C’est lui ! », the preparations ticked, and the search resumed. */
export class PuppyArrivalService {
  /**
   * Fetch the puppy found, if any.
   *
   * @returns The arrival, or null while the search goes on.
   */
  static async read(): Promise<PuppyArrival | null> {
    return ApiClient.get<PuppyArrival | null>('/api/v1/puppy-arrival')
  }

  /**
   * Pause the search on the puppy found, or change its litter or arrival day.
   *
   * @param payload - The litter and the arrival day.
   * @returns The arrival.
   */
  static async start(payload: PuppyArrivalStart): Promise<PuppyArrival> {
    return ApiClient.put<PuppyArrival>('/api/v1/puppy-arrival', payload)
  }

  /**
   * Keep the preparations ticked.
   *
   * @param payload - Keys of the preparations ticked.
   * @returns The arrival.
   */
  static async updateChecklist(payload: PuppyArrivalChecklist): Promise<PuppyArrival> {
    return ApiClient.put<PuppyArrival>('/api/v1/puppy-arrival/checklist', payload)
  }

  /**
   * Resume the search: the litter alerts go out again.
   */
  static async resumeSearch(): Promise<void> {
    await ApiClient.delete('/api/v1/puppy-arrival')
  }
}
