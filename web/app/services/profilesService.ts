import type { Department, SearchProfile, SearchProfileUpdate } from '~/types/api'
import { ApiClient } from './api'

/** HTTP client for the /profiles and /departments API resources. */
export class ProfilesService {
  /**
   * Fetch the search profiles of the user.
   *
   * @returns The profiles, oldest first.
   */
  static async list(): Promise<SearchProfile[]> {
    return ApiClient.get<SearchProfile[]>('/api/v1/profiles')
  }

  /**
   * Save the criteria of a profile; the API re-evaluates every litter.
   *
   * @param profileId - The profile.
   * @param update - The criteria.
   * @returns The saved profile.
   */
  static async update(profileId: number, update: SearchProfileUpdate): Promise<SearchProfile> {
    return ApiClient.put<SearchProfile>(`/api/v1/profiles/${profileId}`, update)
  }

  /**
   * Fetch the French departments, by region.
   *
   * @returns The departments.
   */
  static async listDepartments(): Promise<Department[]> {
    return ApiClient.get<Department[]>('/api/v1/departments')
  }
}
