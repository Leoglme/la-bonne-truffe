import type { ComputedRef, Ref } from 'vue'
import type { LitterCard, LitterDetail } from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { LittersService } from '~/services/littersService'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Filter chips of the home screen. */
export type LitterFilterKey = 'all' | 'preferred' | 'expected'

const PREVIOUS_VISIT_STORAGE_KEY: string = 'lbt-litters-visited-at'

/** Pinia store of the litters: the home list, its filter, and the litter opened in the desktop panel. */
// Pinia ne fournit pas de type nommé pour un store : TypeScript l'élide, il est inécrivable.
// eslint-disable-next-line @typescript-eslint/typedef
export const useLittersStore = defineStore('litters', () => {
  const cards: Ref<LitterCard[]> = ref([])
  const selectedFilterKey: Ref<LitterFilterKey> = ref('all')
  const selectedLitter: Ref<LitterDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(false)
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
    preferredCards.value.filter(
      (card: LitterCard): boolean =>
        card.birth_date !== null && LitterPresentation.isLastNight(card.birth_date, new Date()),
    ),
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
   * Follow a litter (« Suivre »): it starts at « à appeler ».
   *
   * @param litterId - The litter.
   * @returns The updated detail.
   */
  async function follow(litterId: number): Promise<LitterDetail> {
    const detail: LitterDetail = await LittersService.setFollowUp(litterId, { status: 'to_contact' })
    if (selectedLitter.value?.id === litterId) {
      selectedLitter.value = detail
    }
    cards.value = cards.value.map((card: LitterCard): LitterCard =>
      card.id === litterId ? { ...card, follow_up_status: 'to_contact' } : card,
    )
    return detail
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
  }
})
