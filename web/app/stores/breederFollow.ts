import type { Ref } from 'vue'
import type { BreederDetail, BreederFollowUpdate } from '~/types/api'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { BreedersService } from '~/services/breedersService'

/** Pinia store of the dialog that manages the follow of a breeder: its status, reminder, alerts and notes. */
export const useBreederFollowStore = defineStore('breederFollow', () => {
  const openedBreeder: Ref<BreederDetail | null> = ref(null)
  const isSaving: Ref<boolean> = ref(false)

  /**
   * Open the dialog of a breeder.
   *
   * @param breederId - The breeder.
   */
  async function open(breederId: number): Promise<void> {
    openedBreeder.value = await BreedersService.get(breederId)
  }

  /**
   * Open the dialog on a breeder already loaded, without asking the API again.
   *
   * @param breeder - The breeder shown.
   */
  function openWith(breeder: BreederDetail): void {
    openedBreeder.value = breeder
  }

  /**
   * Close the dialog.
   */
  function close(): void {
    openedBreeder.value = null
  }

  /**
   * Save the status, the reminder and the alerts of the opened breeder.
   *
   * @param update - The follow as it should be.
   */
  async function saveFollow(update: BreederFollowUpdate): Promise<void> {
    await saveChange(async (breederId: number): Promise<BreederDetail> =>
      useBreedersStore().saveFollow(breederId, update),
    )
  }

  /**
   * Add a dated note to the opened breeder.
   *
   * @param text - The note.
   */
  async function addNote(text: string): Promise<void> {
    await saveChange((breederId: number): Promise<BreederDetail> => useBreedersStore().addNote(breederId, text))
  }

  /**
   * Delete a note of the opened breeder.
   *
   * @param noteId - The note.
   */
  async function removeNote(noteId: number): Promise<void> {
    await saveChange((breederId: number): Promise<BreederDetail> => useBreedersStore().removeNote(breederId, noteId))
  }

  /**
   * Stop following the opened breeder: its status, reminder, alerts and notes go, and the dialog closes.
   */
  async function stopFollowing(): Promise<void> {
    await saveChange(async (breederId: number): Promise<BreederDetail> => {
      const detail: BreederDetail = await useBreedersStore().removeFollow(breederId)
      close()
      return detail
    })
  }

  /**
   * Send a change of the opened breeder while `isSaving` is up, and show what the API answered.
   *
   * @param change - The call to the breeders store, given the breeder opened.
   */
  async function saveChange(change: (breederId: number) => Promise<BreederDetail>): Promise<void> {
    if (openedBreeder.value === null) {
      return
    }
    const breederId: number = openedBreeder.value.id
    isSaving.value = true
    try {
      const detail: BreederDetail = await change(breederId)
      if (openedBreeder.value?.id === breederId) {
        openedBreeder.value = detail
      }
    } finally {
      isSaving.value = false
    }
  }

  return { openedBreeder, isSaving, open, openWith, close, saveFollow, addNote, removeNote, stopFollowing }
})
