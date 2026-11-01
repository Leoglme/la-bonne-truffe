import type { ComputedRef, Ref } from 'vue'
import type { SourceActivity, SourceStatus } from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { SourcesService } from '~/services/sourcesService'
import { FrenchDate } from '~/utils/frenchDate'
import { SourceRunPresentation } from '~/utils/sourceRunPresentation'

const LIVE_REFRESH_INTERVAL_MS: number = 3000

/** Pinia store of the source statuses (« Relevé il y a 12 min · 1 source en ligne ») and of what runs now. */
export const useSourcesStore = defineStore('sources', () => {
  const statuses: Ref<SourceStatus[]> = ref([])
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)
  const activity: Ref<SourceActivity | null> = ref(null)

  let liveRefreshInterval: ReturnType<typeof setInterval> | null = null
  let isReadingActivity: boolean = false

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
      .map((runAt: string): number => FrenchDate.parseApiDate(runAt).getTime())
    return times.length > 0 ? new Date(Math.max(...times)) : null
  })
  const isEveryCollectedSourceOnline: ComputedRef<boolean> = computed(
    (): boolean => collectedStatuses.value.length > 0 && onlineCount.value === collectedStatuses.value.length,
  )

  /**
   * Load the statuses; a failure keeps the previous ones.
   */
  async function load(): Promise<void> {
    isLoading.value = true
    loadError.value = null
    try {
      statuses.value = await SourcesService.list()
    } catch (error: unknown) {
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Read what runs now; once a relevé ended since the last reading, reload the statuses first, so that its card
   * stops loading with its new line. A failure keeps the last activity: the next reading tries again.
   */
  async function loadActivity(): Promise<void> {
    if (isReadingActivity) {
      return
    }
    isReadingActivity = true
    try {
      const nextActivity: SourceActivity | null = await SourcesService.readActivity().catch((): null => null)
      if (nextActivity === null) {
        return
      }
      if (SourceRunPresentation.hasRunEnded(activity.value, nextActivity)) {
        await load()
      }
      activity.value = nextActivity
    } finally {
      isReadingActivity = false
    }
  }

  /**
   * Show what runs now, as a request of this device just answered it.
   *
   * @param nextActivity - The activity the API answered.
   */
  function applyActivity(nextActivity: SourceActivity): void {
    activity.value = nextActivity
  }

  /**
   * Read what runs now every few seconds while the page is in front, and at once when it comes back: every device
   * shows its buttons loading, wherever the relevé was asked.
   */
  function startLiveUpdates(): void {
    stopLiveUpdates()
    document.addEventListener('visibilitychange', loadActivityWhenShown)
    liveRefreshInterval = setInterval(loadActivityWhenShown, LIVE_REFRESH_INTERVAL_MS)
    loadActivityWhenShown()
  }

  /**
   * Stop reading what runs now, as when the page closes.
   */
  function stopLiveUpdates(): void {
    document.removeEventListener('visibilitychange', loadActivityWhenShown)
    if (liveRefreshInterval !== null) {
      clearInterval(liveRefreshInterval)
      liveRefreshInterval = null
    }
  }

  /**
   * Read what runs now when the page is in front: a hidden page skips its readings.
   */
  function loadActivityWhenShown(): void {
    if (document.visibilityState === 'visible') {
      loadActivity()
    }
  }

  return {
    statuses,
    isLoading,
    loadError,
    activity,
    collectedStatuses,
    onlineCount,
    lastRunAt,
    isEveryCollectedSourceOnline,
    load,
    loadActivity,
    applyActivity,
    startLiveUpdates,
    stopLiveUpdates,
  }
})
