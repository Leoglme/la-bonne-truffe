import type { ComputedRef, Ref } from 'vue'
import type { CoatColor, FollowUpCard, LitterCard, LitterDetail, LitterVisit } from '~/types/api'
import type { LitterBrowsingOrigin, LitterFilterKey, LitterSortKey } from '~/types/Litter'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { DEFAULT_LITTER_FILTER_KEY, LITTER_FILTER_KEYS } from '~/constants/litterFilterOptions'
import { DEFAULT_LITTER_SORT_KEY, LITTER_SORT_KEYS } from '~/constants/litterSortOptions'
import { LittersService } from '~/services/littersService'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'
import { LitterSorting } from '~/utils/litterSorting'
import { SavedChoices } from '~/utils/savedChoices'

const SORT_STORAGE_KEY: string = 'lbt-litter-sort'
const FILTER_STORAGE_KEY: string = 'lbt-litter-filter'

/** Pinia store of the litters: the home list, its filter, sort and search, and the litter opened on the detail screen. */
export const useLittersStore = defineStore('litters', () => {
  const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

  const cards: Ref<LitterCard[]> = ref([])
  const selectedFilterKey: Ref<LitterFilterKey> = ref(DEFAULT_LITTER_FILTER_KEY)
  const selectedSortKey: Ref<LitterSortKey> = ref(DEFAULT_LITTER_SORT_KEY)
  const searchQuery: Ref<string> = ref('')
  const selectedLitter: Ref<LitterDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const previousVisitAt: Ref<Date | null> = ref(null)

  let hasRecordedVisit: boolean = false

  const notDismissedCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    cards.value.filter((card: LitterCard): boolean => card.follow_up_status !== 'dismissed'),
  )

  const filteredCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] => {
    if (selectedFilterKey.value === 'preferred') {
      return notDismissedCards.value.filter((card: LitterCard): boolean => card.tier === 'preferred')
    }
    if (selectedFilterKey.value === 'expected') {
      return notDismissedCards.value.filter((card: LitterCard): boolean => card.kind === 'litter_expected')
    }
    return notDismissedCards.value
  })

  const sortedCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    LitterSorting.sort(filteredCards.value, selectedSortKey.value, locationStore.position),
  )

  const newCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    sortedCards.value.filter((card: LitterCard): boolean => LitterPresentation.isNew(card, previousVisitAt.value)),
  )

  const alreadySeenCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    sortedCards.value.filter((card: LitterCard): boolean => !LitterPresentation.isNew(card, previousVisitAt.value)),
  )

  const visibleCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] => [
    ...newCards.value,
    ...alreadySeenCards.value,
  ])

  const cardsMatchingSearch: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    visibleCards.value.filter((card: LitterCard): boolean =>
      LitterPresentation.matchesSearchQuery(card, searchQuery.value),
    ),
  )

  const preferredCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    notDismissedCards.value.filter((card: LitterCard): boolean => card.tier === 'preferred'),
  )

  const bornLastNightCards: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
    preferredCards.value.filter((card: LitterCard): boolean => LitterPresentation.isBornLastNight(card, new Date())),
  )

  /**
   * Take back the filter and sort of the last visit; the store is built on the server, where storage does not exist.
   */
  function restoreSavedChoices(): void {
    selectedFilterKey.value = SavedChoices.read(FILTER_STORAGE_KEY, LITTER_FILTER_KEYS, DEFAULT_LITTER_FILTER_KEY)
    selectedSortKey.value = SavedChoices.read(SORT_STORAGE_KEY, LITTER_SORT_KEYS, DEFAULT_LITTER_SORT_KEY)
  }

  /**
   * Filter the home list and remember the choice for the next visits.
   *
   * @param filterKey - The chip chosen.
   */
  function selectFilter(filterKey: LitterFilterKey): void {
    selectedFilterKey.value = filterKey
    SavedChoices.keep(FILTER_STORAGE_KEY, filterKey)
  }

  /**
   * Sort the home list and remember the choice for the next visits.
   *
   * @param sortKey - The sort chosen in the drawer.
   */
  function selectSort(sortKey: LitterSortKey): void {
    selectedSortKey.value = sortKey
    SavedChoices.keep(SORT_STORAGE_KEY, sortKey)
  }

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
   * Open a litter on its detail screen.
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
    const breederId: number | null = detail.breeder?.id ?? null
    if (breederId !== null) {
      useBreedersStore()
        .reloadBreeder(breederId)
        .catch((): void => undefined)
    }
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
   * Note the colour of one puppy, or remove it; the API re-scores the litter on the puppies still offered.
   *
   * @param litterId - The litter.
   * @param listingId - The ad of the puppy.
   * @param color - Its colour, null to go back to what its ad says.
   * @returns The updated detail.
   */
  async function confirmPuppyColor(
    litterId: number,
    listingId: number,
    color: CoatColor | null,
  ): Promise<LitterDetail> {
    const detail: LitterDetail = await LittersService.confirmPuppyColor(litterId, listingId, { color })
    applyDetail(detail)
    return detail
  }

  /**
   * Confirm the males and females heard from the breeder, or go back to the sources with both null; re-scored at once.
   *
   * @param litterId - The litter.
   * @param maleCount - Males, null with the females to remove the confirmation.
   * @param femaleCount - Females.
   * @returns The updated detail.
   */
  async function confirmSexes(
    litterId: number,
    maleCount: number | null,
    femaleCount: number | null,
  ): Promise<LitterDetail> {
    const detail: LitterDetail = await LittersService.confirmSexes(litterId, {
      male_count: maleCount,
      female_count: femaleCount,
    })
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
   * @param litterId - The litter shown, looked for in the whole home list when the filter or the search hides it.
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
    const matchingIds: number[] = cardsMatchingSearch.value.map((card: LitterCard): number => card.id)
    return matchingIds.includes(litterId) ? matchingIds : cards.value.map((card: LitterCard): number => card.id)
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
    selectedSortKey,
    searchQuery,
    restoreSavedChoices,
    selectFilter,
    selectSort,
    selectedLitter,
    isLoading,
    loadError,
    previousVisitAt,
    newCards,
    alreadySeenCards,
    visibleCards,
    cardsMatchingSearch,
    preferredCards,
    bornLastNightCards,
    load,
    recordResumeVisit,
    recordVisit,
    select,
    follow,
    confirmColors,
    confirmPuppyColor,
    confirmSexes,
    applyDetail,
    listBrowsableLitterIds,
    followOrOpenFollowUp,
  }
})
