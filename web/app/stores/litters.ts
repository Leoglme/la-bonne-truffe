import type { ComputedRef, Ref } from 'vue'
import type { FollowUpCard, LitterCard, LitterDetail } from '~/types/api'
import type { LitterBrowsingOrigin, LitterFilterKey } from '~/types/Litter'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { LittersService } from '~/services/littersService'
import { LitterPresentation } from '~/utils/litterPresentation'

const PREVIOUS_VISIT_STORAGE_KEY: string = 'lbt-litters-visited-at'

/** Pinia store of the litters: the home list, its filter, and the litter opened on the detail screen or the desktop panel. */
export const useLittersStore = defineStore('litters', () => {
  const cards: Ref<LitterCard[]> = ref([])
  const selectedFilterKey: Ref<LitterFilterKey> = ref('all')
  const selectedLitter: Ref<LitterDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const previousVisitAt: Ref<Date | null> = ref(null)

  const visibleCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] => {
    if (selectedFilterKey.value === 'preferred') {
      return cards.value.filter((card: LitterCard): boolean => card.tier === 'preferred')
    }
    if (selectedFilterKey.value === 'expected') {
      return cards.value.filter((card: LitterCard): boolean => card.kind === 'litter_expected')
    }
    return cards.value
  })

  const preferredCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    cards.value.filter((card: LitterCard): boolean => card.tier === 'preferred'),
  )

  const bornLastNightCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    preferredCards.value.filter((card: LitterCard): boolean => LitterPresentation.isBornLastNight(card, new Date())),
  )

  /**
   * Load the litters, and remember the previous visit for the « Nouveau » badges.
   */
  async function load(): Promise<void> {
    isLoading.value = true
    loadError.value = null
    try {
      if (previousVisitAt.value === null) {
        const storedVisit: string | null = localStorage.getItem(PREVIOUS_VISIT_STORAGE_KEY)
        previousVisitAt.value = storedVisit ? new Date(storedVisit) : null
        localStorage.setItem(PREVIOUS_VISIT_STORAGE_KEY, new Date().toISOString())
      }
      cards.value = await LittersService.list()
    } catch (error: unknown) {
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Open a litter in the desktop detail panel.
   *
   * @param litterId - The litter.
   */
  async function select(litterId: number): Promise<void> {
    selectedLitter.value = await LittersService.get(litterId)
  }

  /**
   * Follow a litter (« Suivre »): it starts at « à appeler ». A litter already followed keeps its follow-up.
   *
   * @param litter - The litter.
   * @returns The detail, updated when the litter was not followed yet.
   */
  async function follow(litter: LitterDetail): Promise<LitterDetail> {
    if (litter.follow_up !== null) {
      return litter
    }
    const detail: LitterDetail = await LittersService.setFollowUp(litter.id, { status: 'to_contact' })
    applyDetail(detail)
    return detail
  }

  /**
   * Write the new detail of a litter into the opened litter, and its follow-up status into its card.
   *
   * @param detail - The detail returned by the API.
   */
  function applyDetail(detail: LitterDetail): void {
    if (selectedLitter.value?.id === detail.id) {
      selectedLitter.value = detail
    }
    cards.value = cards.value.map((card: LitterCard): LitterCard =>
      card.id === detail.id ? { ...card, follow_up_status: detail.follow_up?.status ?? null } : card,
    )
  }

  /**
   * List the litters a swipe on the detail screen goes through, in the order of the screen it was opened from.
   *
   * @param origin - The follow-up screen, or the home list (also for a litter opened from a notification).
   * @param litterId - The litter shown, looked for in the whole home list when the filter hides it.
   * @returns The ids of the litters, in screen order.
   */
  async function listBrowsableLitterIds(origin: LitterBrowsingOrigin, litterId: number): Promise<number[]> {
    if (origin === 'follow-ups') {
      const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()
      if (followUpsStore.cards.length === 0) {
        await followUpsStore.load()
      }
      return followUpsStore.cardsInScreenOrder.map((card: FollowUpCard): number => card.litter.id)
    }
    if (cards.value.length === 0) {
      await load()
    }
    const visibleIds: number[] = visibleCards.value.map((card: LitterCard): number => card.id)
    return visibleIds.includes(litterId) ? visibleIds : cards.value.map((card: LitterCard): number => card.id)
  }

  /**
   * Follow a litter (« Suivre »), or open the drawer of its follow-up once it is followed (« Suivie »).
   *
   * @param litter - The litter.
   * @returns The detail, updated when the litter was just followed.
   */
  async function followOrOpenFollowUp(litter: LitterDetail): Promise<LitterDetail> {
    if (litter.follow_up === null) {
      return follow(litter)
    }
    await useFollowUpsStore().open(litter.id)
    return litter
  }

  return {
    cards,
    selectedFilterKey,
    selectedLitter,
    isLoading,
    loadError,
    previousVisitAt,
    visibleCards,
    preferredCards,
    bornLastNightCards,
    load,
    select,
    follow,
    applyDetail,
    listBrowsableLitterIds,
    followOrOpenFollowUp,
  }
})
