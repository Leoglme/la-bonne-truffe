import type { Ref } from 'vue'
import type { FollowUpCard, FollowUpUpdate, LitterDetail } from '~/types/api'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { LittersService } from '~/services/littersService'

/** Pinia store of the follow-up screen, and of the follow-up drawer. */
export const useFollowUpsStore = defineStore('followUps', () => {
  const cards: Ref<FollowUpCard[]> = ref([])
  const openedLitter: Ref<LitterDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const isSaving: Ref<boolean> = ref(false)

  /**
   * Load the followed litters.
   */
  async function load(): Promise<void> {
    isLoading.value = true
    loadError.value = null
    try {
      cards.value = await LittersService.listFollowUps()
    } catch (error: unknown) {
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Open the drawer of a followed litter.
   *
   * @param litterId - The litter.
   */
  async function open(litterId: number): Promise<void> {
    openedLitter.value = await LittersService.get(litterId)
  }

  /**
   * Close the drawer.
   */
  function close(): void {
    openedLitter.value = null
  }

  /**
   * Save the status and reminder of the opened litter, then refresh the list.
   *
   * @param update - Status and reminder.
   */
  async function saveFollowUp(update: FollowUpUpdate): Promise<void> {
    if (openedLitter.value === null) {
      return
    }
    isSaving.value = true
    try {
      openedLitter.value = await LittersService.setFollowUp(openedLitter.value.id, update)
      await load()
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Add a dated note to the opened litter, then refresh it and the list.
   *
   * @param text - The note.
   */
  async function addNote(text: string): Promise<void> {
    if (openedLitter.value === null) {
      return
    }
    isSaving.value = true
    try {
      await LittersService.addNote(openedLitter.value.id, text)
      openedLitter.value = await LittersService.get(openedLitter.value.id)
      await load()
    } finally {
      isSaving.value = false
    }
  }

  return { cards, openedLitter, isLoading, loadError, isSaving, load, open, close, saveFollowUp, addNote }
})
