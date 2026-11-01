import type {
  BreederCard,
  BreederCreate,
  BreederDetail,
  BreederFollowNote,
  BreederFollowUpdate,
  BreederLinkCreate,
  BreederLinkPreview,
  BreederSearchResults,
  BreederUpdate,
} from '~/types/api'
import { ApiClient } from './api'

const BREEDERS_ENDPOINT: string = '/api/v1/breeders'

/** HTTP client for the /breeders API resource: the directory, the search, the follows and their notes. */
export class BreedersService {
  /**
   * Fetch the breeders worth listing, the most promising first.
   *
   * @returns The cards.
   */
  static async list(): Promise<BreederCard[]> {
    return ApiClient.get<BreederCard[]>(BREEDERS_ENDPOINT)
  }

  /**
   * Fetch the suggestions of the search: breeders, then litters, holding every word typed.
   *
   * @param query - What was typed.
   * @param limit - Breeders and litters kept at most, each.
   * @returns The suggestions, empty for a blank query.
   */
  static async search(query: string, limit: number): Promise<BreederSearchResults> {
    const parameters: URLSearchParams = new URLSearchParams({ q: query, limit: String(limit) })
    return ApiClient.get<BreederSearchResults>(`${BREEDERS_ENDPOINT}/search?${parameters.toString()}`)
  }

  /**
   * Fetch the page of a breeder.
   *
   * @param breederId - The breeder.
   * @returns The detail.
   */
  static async get(breederId: number): Promise<BreederDetail> {
    return ApiClient.get<BreederDetail>(`${BREEDERS_ENDPOINT}/${breederId}`)
  }

  /**
   * Add a breeder by hand, or complete the one the phone or the name already points at.
   *
   * @param payload - Name, place, phone, links, note.
   * @returns The detail of the breeder, followed when asked.
   */
  static async create(payload: BreederCreate): Promise<BreederDetail> {
    return ApiClient.post<BreederDetail>(BREEDERS_ENDPOINT, payload)
  }

  /**
   * Complete a breeder: links, phone, website, notes.
   *
   * @param breederId - The breeder.
   * @param payload - What changes.
   * @returns The updated detail.
   */
  static async update(breederId: number, payload: BreederUpdate): Promise<BreederDetail> {
    return ApiClient.patch<BreederDetail>(`${BREEDERS_ENDPOINT}/${breederId}`, payload)
  }

  /**
   * Ask what a pasted link is, before adding it: a Chiens de France site, a social account or another site.
   *
   * @param breederId - The breeder.
   * @param payload - The link.
   * @returns What the API recognises.
   */
  static async previewLink(breederId: number, payload: BreederLinkCreate): Promise<BreederLinkPreview> {
    return ApiClient.post<BreederLinkPreview>(`${BREEDERS_ENDPOINT}/${breederId}/links/preview`, payload)
  }

  /**
   * Add a pasted link to a breeder; its site on Chiens de France is read at once.
   *
   * @param breederId - The breeder.
   * @param payload - The link.
   * @returns The updated detail.
   */
  static async addLink(breederId: number, payload: BreederLinkCreate): Promise<BreederDetail> {
    return ApiClient.post<BreederDetail>(`${BREEDERS_ENDPOINT}/${breederId}/links`, payload)
  }

  /**
   * Follow a breeder, or change the status, the reminder and the alerts of the follow.
   *
   * @param breederId - The breeder.
   * @param update - Status, reminder and alert settings.
   * @returns The updated detail.
   */
  static async setFollow(breederId: number, update: BreederFollowUpdate): Promise<BreederDetail> {
    return ApiClient.put<BreederDetail>(`${BREEDERS_ENDPOINT}/${breederId}/follow`, update)
  }

  /**
   * Stop following a breeder: its status, reminder, alerts and notes go.
   *
   * @param breederId - The breeder.
   * @returns The detail, without follow.
   */
  static async removeFollow(breederId: number): Promise<BreederDetail> {
    return ApiClient.delete<BreederDetail>(`${BREEDERS_ENDPOINT}/${breederId}/follow`)
  }

  /**
   * Add a dated note to the follow of a breeder.
   *
   * @param breederId - The breeder.
   * @param text - The note.
   * @returns The stored note.
   */
  static async addNote(breederId: number, text: string): Promise<BreederFollowNote> {
    return ApiClient.post<BreederFollowNote>(`${BREEDERS_ENDPOINT}/${breederId}/notes`, { text })
  }

  /**
   * Delete a note of the follow of a breeder.
   *
   * @param breederId - The breeder.
   * @param noteId - The note.
   */
  static async removeNote(breederId: number, noteId: number): Promise<void> {
    await ApiClient.delete(`${BREEDERS_ENDPOINT}/${breederId}/notes/${noteId}`)
  }
}
