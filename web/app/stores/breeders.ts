import type { ComputedRef, Ref } from 'vue'
import type {
  BreederCard,
  BreederCreate,
  BreederDetail,
  BreederFilter,
  BreederFollowUpdate,
  BreederSearchResults,
  BreederSort,
  BreederUpdate,
} from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  BREEDER_FILTER_KEYS,
  BREEDER_SORT_KEYS,
  DEFAULT_BREEDER_FILTER_KEY,
  DEFAULT_BREEDER_FOLLOW,
  DEFAULT_BREEDER_SORT_KEY,
} from '~/constants/breederOptions'
import { BreedersService } from '~/services/breedersService'
import { BreederPresentation } from '~/utils/breederPresentation'
import { SavedChoices } from '~/utils/savedChoices'

const SEARCH_SUGGESTIONS_LIMIT: number = 8
const FILTER_STORAGE_KEY: string = 'lbt-breeder-filter'
const SORT_STORAGE_KEY: string = 'lbt-breeder-sort'

/** Pinia store of the breeders: the directory list, its filter and sort, the search, and the breeder opened. */
export const useBreedersStore = defineStore('breeders', () => {
  const cards: Ref<BreederCard[]> = ref([])
  const selectedFilterKey: Ref<BreederFilter> = ref(DEFAULT_BREEDER_FILTER_KEY)
  const selectedSortKey: Ref<BreederSort> = ref(DEFAULT_BREEDER_SORT_KEY)
  const selectedBreeder: Ref<BreederDetail | null> = ref(null)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const searchQuery: Ref<string> = ref('')
  const searchResults: Ref<BreederSearchResults | null> = ref(null)
  const isSearching: Ref<boolean> = ref(false)
  const searchError: Ref<string | null> = ref(null)

  const filteredCards: ComputedRef<BreederCard[]> = computed((): BreederCard[] =>
    cards.value.filter((card: BreederCard): boolean => BreederPresentation.passesFilter(card, selectedFilterKey.value)),
  )

  const visibleCards: ComputedRef<BreederCard[]> = computed((): BreederCard[] =>
    selectedSortKey.value === 'name'
      ? [...filteredCards.value].sort((first: BreederCard, second: BreederCard): number =>
          first.name.localeCompare(second.name, 'fr'),
        )
      : filteredCards.value,
  )

  const followedCards: ComputedRef<BreederCard[]> = computed((): BreederCard[] =>
    cards.value.filter((card: BreederCard): boolean => card.is_followed),
  )

  /**
   * Load the breeders of the directory, the most promising first.
   */
  async function load(): Promise<void> {
    isLoading.value = true
    loadError.value = null
    try {
      cards.value = await BreedersService.list()
    } catch (error: unknown) {
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Take back the filter and sort of the last visit; the store is built on the server, where storage does not exist.
   */
  function restoreSavedChoices(): void {
    selectedFilterKey.value = SavedChoices.read(FILTER_STORAGE_KEY, BREEDER_FILTER_KEYS, DEFAULT_BREEDER_FILTER_KEY)
    selectedSortKey.value = SavedChoices.read(SORT_STORAGE_KEY, BREEDER_SORT_KEYS, DEFAULT_BREEDER_SORT_KEY)
  }

  /**
   * Filter the list and remember the choice for the next visits.
   *
   * @param filterKey - The chip chosen.
   */
  function selectFilter(filterKey: BreederFilter): void {
    selectedFilterKey.value = filterKey
    SavedChoices.keep(FILTER_STORAGE_KEY, filterKey)
  }

  /**
   * Sort the list and remember the choice for the next visits.
   *
   * @param sortKey - The sort chosen.
   */
  function selectSort(sortKey: BreederSort): void {
    selectedSortKey.value = sortKey
    SavedChoices.keep(SORT_STORAGE_KEY, sortKey)
  }

  /**
   * Ask the API for the suggestions of what was typed; a blank query clears them.
   *
   * @param query - What was typed.
   */
  async function search(query: string): Promise<void> {
    searchQuery.value = query
    searchError.value = null
    if (query.trim() === '') {
      searchResults.value = null
      isSearching.value = false
      return
    }
    isSearching.value = true
    try {
      const results: BreederSearchResults = await BreedersService.search(query, SEARCH_SUGGESTIONS_LIMIT)
      if (searchQuery.value === query) {
        searchResults.value = results
      }
    } catch (error: unknown) {
      searchError.value = error instanceof Error ? error.message : 'Recherche impossible'
    } finally {
      if (searchQuery.value === query) {
        isSearching.value = false
      }
    }
  }

  /**
   * Forget the search and its suggestions.
   */
  function clearSearch(): void {
    searchQuery.value = ''
    searchResults.value = null
    searchError.value = null
    isSearching.value = false
  }

  /**
   * Open a breeder on the detail screen.
   *
   * @param breederId - The breeder.
   */
  async function select(breederId: number): Promise<void> {
    selectedBreeder.value = await BreedersService.get(breederId)
  }

  /**
   * Follow a breeder with the default alerts, or keep the follow it already has.
   *
   * @param breeder - The breeder.
   * @returns The detail, updated when the breeder was not followed yet.
   */
  async function follow(breeder: BreederDetail): Promise<BreederDetail> {
    if (breeder.follow !== null) {
      return breeder
    }
    const detail: BreederDetail = await BreedersService.setFollow(breeder.id, { ...DEFAULT_BREEDER_FOLLOW })
    applyDetail(detail)
    return detail
  }

  /**
   * Change the status, the reminder or the alerts of a followed breeder.
   *
   * @param breederId - The breeder.
   * @param update - The follow as it should be.
   * @returns The updated detail.
   */
  async function saveFollow(breederId: number, update: BreederFollowUpdate): Promise<BreederDetail> {
    const detail: BreederDetail = await BreedersService.setFollow(breederId, update)
    applyDetail(detail)
    return detail
  }

  /**
   * Stop following a breeder.
   *
   * @param breederId - The breeder.
   * @returns The detail, without follow.
   */
  async function removeFollow(breederId: number): Promise<BreederDetail> {
    const detail: BreederDetail = await BreedersService.removeFollow(breederId)
    applyDetail(detail)
    return detail
  }

  /**
   * Add a dated note to the follow of a breeder, then reload its page.
   *
   * @param breederId - The breeder.
   * @param text - The note.
   * @returns The reloaded detail.
   */
  async function addNote(breederId: number, text: string): Promise<BreederDetail> {
    await BreedersService.addNote(breederId, text)
    const detail: BreederDetail = await BreedersService.get(breederId)
    applyDetail(detail)
    return detail
  }

  /**
   * Delete a note of the follow of a breeder, then reload its page.
   *
   * @param breederId - The breeder.
   * @param noteId - The note.
   * @returns The reloaded detail.
   */
  async function removeNote(breederId: number, noteId: number): Promise<BreederDetail> {
    await BreedersService.removeNote(breederId, noteId)
    const detail: BreederDetail = await BreedersService.get(breederId)
    applyDetail(detail)
    return detail
  }

  /**
   * Add a breeder by hand, then reload the list so that it appears in it.
   *
   * @param payload - Name, place, phone, links, note.
   * @returns The detail of the breeder created or completed.
   */
  async function createManual(payload: BreederCreate): Promise<BreederDetail> {
    const detail: BreederDetail = await BreedersService.create(payload)
    await load()
    return detail
  }

  /**
   * Complete a breeder: links, phone, website, notes.
   *
   * @param breederId - The breeder.
   * @param payload - What changes.
   * @returns The updated detail.
   */
  async function update(breederId: number, payload: BreederUpdate): Promise<BreederDetail> {
    const detail: BreederDetail = await BreedersService.update(breederId, payload)
    applyDetail(detail)
    return detail
  }

  /**
   * Add a pasted link to a breeder, wherever it is shown.
   *
   * @param breederId - The breeder.
   * @param url - The link as pasted.
   * @returns The updated detail.
   */
  async function addLink(breederId: number, url: string): Promise<BreederDetail> {
    const detail: BreederDetail = await BreedersService.addLink(breederId, { url })
    applyDetail(detail)
    return detail
  }

  /**
   * Read a breeder again from the API, then write it wherever it is shown.
   *
   * @param breederId - The breeder.
   */
  async function reloadBreeder(breederId: number): Promise<void> {
    applyDetail(await BreedersService.get(breederId))
  }

  /**
   * Write a new detail into the list, the detail screen and the suggestions, wherever the breeder is shown.
   *
   * @param detail - The detail returned by the API.
   */
  function applyDetail(detail: BreederDetail): void {
    cards.value = cards.value.map((card: BreederCard): BreederCard => (card.id === detail.id ? detail : card))
    if (selectedBreeder.value?.id === detail.id) {
      selectedBreeder.value = detail
    }
    if (searchResults.value !== null) {
      searchResults.value = {
        ...searchResults.value,
        breeders: searchResults.value.breeders.map((card: BreederCard): BreederCard =>
          card.id === detail.id ? detail : card,
        ),
      }
    }
  }

  return {
    cards,
    selectedFilterKey,
    selectedSortKey,
    selectedBreeder,
    isLoading,
    loadError,
    searchQuery,
    searchResults,
    isSearching,
    searchError,
    filteredCards,
    visibleCards,
    followedCards,
    load,
    restoreSavedChoices,
    selectFilter,
    selectSort,
    search,
    clearSearch,
    select,
    follow,
    saveFollow,
    removeFollow,
    addNote,
    removeNote,
    createManual,
    update,
    addLink,
    reloadBreeder,
    applyDetail,
  }
})
