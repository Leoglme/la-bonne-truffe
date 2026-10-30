import type { Ref } from 'vue'
import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  RelayedPageResponse,
  RelayPageRequest,
} from '~/types/api'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { TokenRejectedError } from '~/services/authService'
import { DesktopPageReaderService } from '~/services/desktopPageReaderService'
import { SourcesService } from '~/services/sourcesService'
import { CentraleCanineRelayRunner } from '~/utils/centraleCanineRelayRunner'

const FIRST_CHECK_DELAY_MS: number = 30_000
const CHECK_INTERVAL_MS: number = 5 * 60_000
const LOGIN_PATH: string = '/connexion'

/** Pinia store of the Centrale Canine relay: the desktop app reads it in the background, when a run is due. */
export const useCentraleCanineRelayStore = defineStore('centraleCanineRelay', () => {
  const lastRelayErrorMessage: Ref<string | null> = ref(null)

  let isRelaying: boolean = false
  let nextCheckTimer: ReturnType<typeof setTimeout> | null = null
  let isWatching: boolean = false

  /**
   * Relay once, after the session check the hidden window never makes by itself; a refused session shows the login screen.
   *
   * @param isRequestedByUser - « Relever maintenant »: run even when the last run is recent.
   * @returns The last answer of the API, or null when nothing was sent.
   */
  async function relay(isRequestedByUser: boolean): Promise<CentraleCanineRelayAnswer | null> {
    const userStore: ReturnType<typeof useUserStore> = useUserStore()

    if (isRelaying || !userStore.token) {
      return null
    }
    const hasValidSession: boolean = await userStore.validateSession()

    if (!hasValidSession) {
      if (!userStore.token) {
        await signOut()
      }
      return null
    }
    isRelaying = true
    try {
      const answer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
        {
          sendRelayRequest: (relayRequest: CentraleCanineRelayRequest): Promise<CentraleCanineRelayAnswer> =>
            SourcesService.relayCentraleCanine(relayRequest),
          readPageWithCurl: (pageRequest: RelayPageRequest): Promise<RelayedPageResponse> =>
            DesktopPageReaderService.readCentraleCaninePageWithCurl(pageRequest),
          readPageInBrowser: (pageRequest: RelayPageRequest): Promise<RelayedPageResponse> =>
            DesktopPageReaderService.readCentraleCaninePageInBrowser(pageRequest),
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
      if (error instanceof TokenRejectedError) {
        await signOut()
      } else {
        lastRelayErrorMessage.value = error instanceof Error ? error.message : 'Relais impossible'
      }
      throw error
    } finally {
      isRelaying = false
    }
  }

  /**
   * Stop relaying and show the login screen: the API refused the session of this computer.
   */
  async function signOut(): Promise<void> {
    stopWatching()
    useUserStore().logout()
    await navigateTo(LOGIN_PATH)
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
