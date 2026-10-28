import type { Ref } from 'vue'
import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  RelayedPageResponse,
  RelayPageRequest,
} from '~/types/api'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { DesktopCurlService } from '~/services/desktopCurlService'
import { SourcesService } from '~/services/sourcesService'
import { CentraleCanineRelayRunner } from '~/utils/centraleCanineRelayRunner'

const FIRST_CHECK_DELAY_MS: number = 30_000
const CHECK_INTERVAL_MS: number = 5 * 60_000

/** Pinia store of the Centrale Canine relay: the desktop app reads it in the background, when a run is due. */
export const useCentraleCanineRelayStore = defineStore('centraleCanineRelay', () => {
  const lastRelayErrorMessage: Ref<string | null> = ref(null)

  let isRelaying: boolean = false
  let nextCheckTimer: ReturnType<typeof setTimeout> | null = null
  let isWatching: boolean = false

  /**
   * Relay once, unless a relay already runs on this computer or nobody is signed in.
   *
   * @param isRequestedByUser - « Relever maintenant »: run even when the last run is recent.
   * @returns The last answer of the API, or null when nothing was sent.
   */
  async function relay(isRequestedByUser: boolean): Promise<CentraleCanineRelayAnswer | null> {
    if (isRelaying || !useUserStore().token) {
      return null
    }
    isRelaying = true
    try {
      const answer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
        {
          sendRelayRequest: (relayRequest: CentraleCanineRelayRequest): Promise<CentraleCanineRelayAnswer> =>
            SourcesService.relayCentraleCanine(relayRequest),
          readPageWithCurl: (pageRequest: RelayPageRequest): Promise<RelayedPageResponse> =>
            DesktopCurlService.readCentraleCaninePage(pageRequest),
          pause: (milliseconds: number): Promise<void> =>
            new Promise((resolve: () => void): void => {
              setTimeout(resolve, milliseconds)
            }),
        },
        isRequestedByUser,
      )
      lastRelayErrorMessage.value = null
      if (answer.state === 'run_finished') {
        useSourcesStore().statuses = answer.source_statuses
      }
      return answer
    } catch (error: unknown) {
      lastRelayErrorMessage.value = error instanceof Error ? error.message : 'Relais impossible'
      throw error
    } finally {
      isRelaying = false
    }
  }

  /**
   * Check later whether a run is due; a failed relay waits for the next check.
   *
   * @param delayMs - Time before the check.
   */
  function scheduleCheck(delayMs: number): void {
    nextCheckTimer = setTimeout(async (): Promise<void> => {
      await relay(false).catch((): null => null)
      if (isWatching) {
        scheduleCheck(CHECK_INTERVAL_MS)
      }
    }, delayMs)
  }

  /**
   * Start checking every few minutes whether the Centrale Canine run of the hour is due.
   */
  function startWatching(): void {
    if (isWatching) {
      return
    }
    isWatching = true
    scheduleCheck(FIRST_CHECK_DELAY_MS)
  }

  /**
   * Stop the checks, as when the user signs out.
   */
  function stopWatching(): void {
    isWatching = false
    if (nextCheckTimer !== null) {
      clearTimeout(nextCheckTimer)
      nextCheckTimer = null
    }
  }

  return {
    lastRelayErrorMessage,
    relay,
    startWatching,
    stopWatching,
  }
})
