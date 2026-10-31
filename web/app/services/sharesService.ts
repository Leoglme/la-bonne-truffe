import type { LitterShareCreate, LitterShareLink, SharedLitter } from '~/types/api'
import { ApiClient } from './api'

/** HTTP client for the shared links of a litter: create one, and read the page it opens. */
export class SharesService {
  /**
   * Create the link of a litter, valid thirty days.
   *
   * @param litterId - The litter.
   * @param message - Word for the people the link goes to, null for none.
   * @returns The link to send.
   */
  static async create(litterId: number, message: string | null): Promise<LitterShareLink> {
    const payload: LitterShareCreate = { message }
    return ApiClient.post<LitterShareLink>(`/api/v1/litters/${litterId}/shares`, payload)
  }

  /**
   * Read the page of a shared link; no account needed.
   *
   * @param token - Secret part of the link.
   * @returns The litter, the first name of who shared it and their word.
   */
  static async read(token: string): Promise<SharedLitter> {
    return ApiClient.get<SharedLitter>(`/api/v1/shares/${encodeURIComponent(token)}`)
  }
}
