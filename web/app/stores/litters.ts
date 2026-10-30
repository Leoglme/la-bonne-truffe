import type { ComputedRef, Ref } from 'vue'
import type { CoatColor, FollowUpCard, LitterCard, LitterDetail, LitterVisit } from '~/types/api'
import type { LitterBrowsingOrigin, LitterFilterKey } from '~/types/Litter'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { LittersService } from '~/services/littersService'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Pinia store of the litters: the home list, its filter, and the litter opened on the detail screen or the desktop panel. */
export const useLittersStore = defineStore('litters', () => {
  const cards: Ref<LitterCard[]> = ref([])
  const selectedFilterKey: Ref<LitterFilterKey> = ref('all')
  const selectedLitter: Ref<LitterDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const previousVisitAt: Ref<Date | null> = ref(null)

  let hasRecordedVisit: boolean = false

  const filteredCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] => {
    if (selectedFilterKey.value === 'preferred') {
      return cards.value.filter((card: LitterCard): boolean => card.tier === 'preferred')
    }
    if (selectedFilterKey.value === 'expected') {
      return cards.value.filter((card: LitterCard): boolean => card.kind === 'litter_expected')
    }
    return cards.value
  })

  const newCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    filteredCards.value.filter((card: LitterCard): boolean => LitterPresentation.isNew(card, previousVisitAt.value)),
  )

  const alreadySeenCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    filteredCards.value.filter((card: LitterCard): boolean => !LitterPresentation.isNew(card, previousVisitAt.value)),
  )

  const visibleCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] => [
    ...newCards.value,
    ...alreadySeenCards.value,
  ])

  const preferredCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    cards.value.filter((card: LitterCard): boolean => card.tier === 'preferred'),
  )

  const bornLastNightCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    preferredCards.value.filter((card: LitterCard): boolean => LitterPresentation.isBornLastNight(card, new Date())),
  )

  /**
   * Load the litters of the home list.
   */
  async function load(): Promise<void> {
    isLoading.value = true
    loadError.value = null
    try {
      cards.value = await LittersService.list()
    } catch (error: unknown) {
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Record a look at the home list after a resume, as a new launch: the « Nouveau » badges move to what came since.
   */
  async function recordResumeVisit(): Promise<void> {
    hasRecordedVisit = false
    await recordVisit()
  }

  /**
   * Record the look at the home list once per launch of the app, and keep the previous one to tell the new litters.
   */
  async function recordVisit(): Promise<void> {
    if (hasRecordedVisit) {
      return
    }
    hasRecordedVisit = true
    try {
      const visit: LitterVisit = await LittersService.recordVisit()
      previousVisitAt.value = visit.previous_visit_at ? FrenchDate.parseApiDate(visit.previous_visit_at) : null
    } catch (error: unknown) {
      hasRecordedVisit = false
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
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
   * Confirm the colour heard from the breeder, or remove the confirmation; the API re-scores the litter at once.
   *
   * @param litterId - The litter.
   * @param colors - The confirmed colours, none to go back to what the sources say.
   * @returns The updated detail.
   */
  async function confirmColors(litterId: number, colors: CoatColor[]): Promise<LitterDetail> {
    const detail: LitterDetail = await LittersService.confirmColors(litterId, { colors })
    applyDetail(detail)
    return detail
  }

  /**
   * Write the new detail of a litter into the opened litter, and its fresh facts (colours, score, follow-up) into its card.
   *
   * @param detail - The detail returned by the API.
   */
  function applyDetail(detail: LitterDetail): void {
    if (selectedLitter.value?.id === detail.id) {
      selectedLitter.value = detail
    }
    cards.value = cards.value.map((card: LitterCard): LitterCard =>
      card.id === detail.id ? { ...card, ...detail } : card,
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
    newCards,
    alreadySeenCards,
    visibleCards,
    preferredCards,
    bornLastNightCards,
    load,
    recordResumeVisit,
    recordVisit,
    select,
    follow,
    confirmColors,
    applyDetail,
    listBrowsableLitterIds,
    followOrOpenFollowUp,
  }
})
