import type { ComputedRef, Ref } from 'vue'
import type { FollowUpCard, FollowUpUpdate, LitterDetail } from '~/types/api'
import type { FollowUpSection } from '~/types/FollowUp'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { FOLLOW_UP_SECTIONS } from '~/constants/followUpOptions'
import { LittersService } from '~/services/littersService'

/** Pinia store of the follow-up screen, and of the follow-up drawer. */
export const useFollowUpsStore = defineStore('followUps', () => {
  const cards: Ref<FollowUpCard[]> = ref([])
  const openedLitter: Ref<LitterDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const isSaving: Ref<boolean> = ref(false)

  const cardsInScreenOrder: ComputedRef<FollowUpCard[]> = computed((): FollowUpCard[] =>
    FOLLOW_UP_SECTIONS.flatMap((section: FollowUpSection): FollowUpCard[] =>
      cards.value.filter((card: FollowUpCard): boolean => section.statuses.includes(card.status)),
    ),
  )

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
    const litterId: number = openedLitter.value.id
    await saveChange(async (): Promise<void> => {
      setOpenedLitter(await LittersService.setFollowUp(litterId, update))
    })
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
    const litterId: number = openedLitter.value.id
    await saveChange(async (): Promise<void> => {
      await LittersService.addNote(litterId, text)
      setOpenedLitter(await LittersService.get(litterId))
    })
  }

  /**
   * Delete a note of the opened litter, then refresh it and the list.
   *
   * @param noteId - The note.
   */
  async function removeNote(noteId: number): Promise<void> {
    if (openedLitter.value === null) {
      return
    }
    const litterId: number = openedLitter.value.id
    await saveChange(async (): Promise<void> => {
      await LittersService.removeNote(litterId, noteId)
      setOpenedLitter(await LittersService.get(litterId))
    })
  }

  /**
   * Stop following the opened litter: its status, reminder and notes go, and the drawer closes.
   */
  async function stopFollowing(): Promise<void> {
    if (openedLitter.value === null) {
      return
    }
    const litterId: number = openedLitter.value.id
    await saveChange(async (): Promise<void> => {
      useLittersStore().applyDetail(await LittersService.removeFollowUp(litterId))
      close()
    })
  }

  /**
   * Send a change of the opened litter while `isSaving` is up, then reload the list.
   *
   * @param change - The calls to the API.
   */
  async function saveChange(change: () => Promise<void>): Promise<void> {
    isSaving.value = true
    try {
      await change()
      await load()
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Write the new detail of the opened litter into the drawer, then into the litters store.
   *
   * @param detail - The detail returned by the API.
   */
  function setOpenedLitter(detail: LitterDetail): void {
    openedLitter.value = detail
    useLittersStore().applyDetail(detail)
  }

  return {
    cards,
    openedLitter,
    isLoading,
    loadError,
    isSaving,
    cardsInScreenOrder,
    load,
    open,
    close,
    saveFollowUp,
    addNote,
    removeNote,
    stopFollowing,
  }
})
