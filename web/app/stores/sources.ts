import type { ComputedRef, Ref } from 'vue'
import type { SourceStatus } from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { SourcesService } from '~/services/sourcesService'

/** Pinia store of the source statuses: « Relevé il y a 12 min · 1 source en ligne ». */
// Pinia ne fournit pas de type nommé pour un store : TypeScript l'élide, il est inécrivable.
// eslint-disable-next-line @typescript-eslint/typedef
export const useSourcesStore = defineStore('sources', () => {
  const statuses: Ref<SourceStatus[]> = ref([])

  const collectedStatuses: ComputedRef<SourceStatus[]> = computed((): SourceStatus[] =>
    statuses.value.filter((status: SourceStatus): boolean => status.is_collected),
  )
  const onlineCount: ComputedRef<number> = computed(
    (): number => collectedStatuses.value.filter((status: SourceStatus): boolean => status.last_status === 'ok').length,
  )
  const lastRunAt: ComputedRef<Date | null> = computed((): Date | null => {
    const times: number[] = collectedStatuses.value
      .map((status: SourceStatus): string | null => status.last_run_at)
      .filter((runAt: string | null): runAt is string => runAt !== null)
      .map((runAt: string): number => new Date(`${runAt}Z`).getTime())
    return times.length > 0 ? new Date(Math.max(...times)) : null
  })
  const isEveryCollectedSourceOnline: ComputedRef<boolean> = computed(
    (): boolean => collectedStatuses.value.length > 0 && onlineCount.value === collectedStatuses.value.length,
  )

  /**
   * Load the statuses; a failure keeps the previous ones.
   */
  async function load(): Promise<void> {
    try {
      statuses.value = await SourcesService.list()
    } catch {
      // The status line simply stays as it was.
    }
  }

  return { statuses, collectedStatuses, onlineCount, lastRunAt, isEveryCollectedSourceOnline, load }
})
