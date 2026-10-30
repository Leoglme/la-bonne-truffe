import type {
  ColorConfirmation,
  FollowUpCard,
  FollowUpNote,
  FollowUpUpdate,
  LitterCard,
  LitterDetail,
  LitterVisit,
} from '~/types/api'
import { ApiClient } from './api'

/** HTTP client for the /litters and /follow-ups API resources. */
export class LittersService {
  /**
   * Fetch the litters of the home screen, best score first.
   *
   * @returns The cards.
   */
  static async list(): Promise<LitterCard[]> {
    return ApiClient.get<LitterCard[]>('/api/v1/litters')
  }

  /**
   * Record that the home list is looked at now, on whatever device.
   *
   * @returns The previous look: the litters first seen after it are the new ones.
   */
  static async recordVisit(): Promise<LitterVisit> {
    return ApiClient.post<LitterVisit>('/api/v1/litters/visit', {})
  }

  /**
   * Fetch the detail of a litter.
   *
   * @param litterId - The litter.
   * @returns The detail.
   */
  static async get(litterId: number): Promise<LitterDetail> {
    return ApiClient.get<LitterDetail>(`/api/v1/litters/${litterId}`)
  }

  /**
   * Confirm the colours of a litter after a call.
   *
   * @param litterId - The litter.
   * @param confirmation - Confirmed colours.
   * @returns The updated detail.
   */
  static async confirmColors(litterId: number, confirmation: ColorConfirmation): Promise<LitterDetail> {
    return ApiClient.patch<LitterDetail>(`/api/v1/litters/${litterId}/colors`, confirmation)
  }

  /**
   * Follow a litter, or change where the exchange stands.
   *
   * @param litterId - The litter.
   * @param update - Status and reminder.
   * @returns The updated detail.
   */
  static async setFollowUp(litterId: number, update: FollowUpUpdate): Promise<LitterDetail> {
    return ApiClient.put<LitterDetail>(`/api/v1/litters/${litterId}/follow-up`, update)
  }

  /**
   * Stop following a litter: its status, reminder and notes are deleted.
   *
   * @param litterId - The litter.
   * @returns The detail, without follow-up.
   */
  static async removeFollowUp(litterId: number): Promise<LitterDetail> {
    return ApiClient.delete<LitterDetail>(`/api/v1/litters/${litterId}/follow-up`)
  }

  /**
   * Add a dated note to the follow-up of a litter.
   *
   * @param litterId - The litter.
   * @param text - The note.
   * @returns The stored note.
   */
  static async addNote(litterId: number, text: string): Promise<FollowUpNote> {
    return ApiClient.post<FollowUpNote>(`/api/v1/litters/${litterId}/notes`, { text })
  }

  /**
   * Delete a note of the follow-up of a litter.
   *
   * @param litterId - The litter.
   * @param noteId - The note.
   */
  static async removeNote(litterId: number, noteId: number): Promise<void> {
    await ApiClient.delete(`/api/v1/litters/${litterId}/notes/${noteId}`)
  }

  /**
   * Fetch the followed litters, next reminder first.
   *
   * @returns The follow-up cards.
   */
  static async listFollowUps(): Promise<FollowUpCard[]> {
    return ApiClient.get<FollowUpCard[]>('/api/v1/follow-ups')
  }
}
