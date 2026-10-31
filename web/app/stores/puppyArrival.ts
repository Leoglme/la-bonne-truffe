import type { ComputedRef, Ref } from 'vue'
import type { LitterDetail, PuppyArrival } from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { LittersService } from '~/services/littersService'
import { PuppyArrivalService } from '~/services/puppyArrivalService'

/** Pinia store of the puppy found: its arrival, its litter, and the preparations ticked. */
export const usePuppyArrivalStore = defineStore('puppyArrival', () => {
  const arrival: Ref<PuppyArrival | null> = ref(null)
  const litter: Ref<LitterDetail | null> = ref(null)

  const isSearchPaused: ComputedRef<boolean> = computed((): boolean => arrival.value !== null)

  /**
   * Load the puppy found and show it with its litter at once; when it cannot be read, what is shown stays.
   */
  async function load(): Promise<void> {
    let loadedArrival: PuppyArrival | null
    try {
      loadedArrival = await PuppyArrivalService.read()
    } catch {
      return
    }
    litter.value = await readLitter(loadedArrival)
    arrival.value = loadedArrival
  }

  /**
   * Read the litter of the puppy, for its photo and its breeder.
   *
   * @param puppyArrival - The puppy found, or null while the search goes on.
   * @returns Its litter, or null when there is none or it cannot be read: the screen does without it.
   */
  async function readLitter(puppyArrival: PuppyArrival | null): Promise<LitterDetail | null> {
    const litterId: number | null = puppyArrival?.litter_group_id ?? null
    if (litterId === null) {
      return null
    }
    try {
      return await LittersService.get(litterId)
    } catch {
      return null
    }
  }

  /**
   * « C’est lui ! » : pause the search on the puppy of a litter.
   *
   * @param litterId - Litter of the puppy.
   * @param arrivalOn - Day it comes home, as a date input holds it.
   */
  async function start(litterId: number, arrivalOn: string): Promise<void> {
    const startedArrival: PuppyArrival = await PuppyArrivalService.start({
      litter_group_id: litterId,
      arrival_on: arrivalOn,
    })
    litter.value = await readLitter(startedArrival)
    arrival.value = startedArrival
  }

  /**
   * Tick or untick a preparation; the tick shows at once and goes back if the API refuses it.
   *
   * @param preparationKey - The preparation.
   * @throws Error when the API refuses the change.
   */
  async function togglePreparation(preparationKey: string): Promise<void> {
    if (arrival.value === null) {
      return
    }
    const previousArrival: PuppyArrival = arrival.value
    const donePreparationKeys: string[] = previousArrival.done_items.includes(preparationKey)
      ? previousArrival.done_items.filter(
          (donePreparationKey: string): boolean => donePreparationKey !== preparationKey,
        )
      : [...previousArrival.done_items, preparationKey]
    arrival.value = { ...previousArrival, done_items: donePreparationKeys }
    try {
      arrival.value = await PuppyArrivalService.updateChecklist({ done_items: donePreparationKeys })
    } catch (error: unknown) {
      arrival.value = previousArrival
      throw error
    }
  }

  /**
   * Resume the search: the home lists the litters again and the alerts go out.
   */
  async function resumeSearch(): Promise<void> {
    await PuppyArrivalService.resumeSearch()
    arrival.value = null
    litter.value = null
  }

  return { arrival, litter, isSearchPaused, load, start, togglePreparation, resumeSearch }
})
