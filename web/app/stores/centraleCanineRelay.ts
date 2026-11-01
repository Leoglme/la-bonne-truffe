import type { Ref } from 'vue'
import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  RelayedPageResponse,
  RelayPageRequest,
} from '~/types/api'
import type { CentraleCanineRelayProgress } from '~/types/CentraleCanineRelay'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { TokenRejectedError } from '~/services/authService'
import { DesktopPageReaderService } from '~/services/desktopPageReaderService'
import { SourcesService } from '~/services/sourcesService'
import { CentraleCanineRelayRunner } from '~/utils/centraleCanineRelayRunner'

const FIRST_CHECK_DELAY_MS: number = 30_000
const CHECK_INTERVAL_MS: number = 15_000
const LOGIN_PATH: string = '/connexion'

/**
 * Pinia store of the Centrale Canine relay: the desktop app checks every fifteen seconds whether a run is due or
 * asked from another device, and relays it in the background.
 */
export const useCentraleCanineRelayStore = defineStore('centraleCanineRelay', () => {
  const lastRelayErrorMessage: Ref<string | null> = ref(null)
  const isRelaying: Ref<boolean> = ref(false)
  const relayProgress: Ref<CentraleCanineRelayProgress | null> = ref(null)

  let nextCheckTimer: ReturnType<typeof setTimeout> | null = null
  let isWatching: boolean = false
  let relayCall: Promise<CentraleCanineRelayAnswer | null> | null = null

  /**
   * Relay once, after any relay call already under way here: a check of the timer gives way to it, a request of
   * the user waits for it to end.
   *
   * @param isRequestedByUser - « Relever maintenant »: every source runs, even when its last run is recent.
   * @returns The last answer of the API, or null when nothing was sent: a check while a call runs, or no session.
   */
  async function relay(isRequestedByUser: boolean): Promise<CentraleCanineRelayAnswer | null> {
    while (relayCall !== null) {
      if (!isRequestedByUser) {
        return null
      }
      await relayCall.catch((): null => null)
    }
    relayCall = relayOnce(isRequestedByUser)
    try {
      return await relayCall
    } finally {
      relayCall = null
    }
  }

  /**
   * Relay once, after the session check the hidden window never makes by itself; a refused session shows the
   * login screen. The relay shows from its first page to read, so that a check finding nothing due stays unseen.
   *
   * @param isRequestedByUser - « Relever maintenant »: every source runs, even when its last run is recent.
   * @returns The last answer of the API, or null when there is no session.
   */
  async function relayOnce(isRequestedByUser: boolean): Promise<CentraleCanineRelayAnswer | null> {
    const userStore: ReturnType<typeof useUserStore> = useUserStore()

    if (!userStore.token) {
      return null
    }
    const hasValidSession: boolean = await userStore.validateSession()

    if (!hasValidSession) {
      if (!userStore.token) {
        await signOut()
      }
      return null
    }
    relayProgress.value = null
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
          reportProgress: (progress: CentraleCanineRelayProgress): void => {
            isRelaying.value = true
            relayProgress.value = progress
          },
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
      if (isRelaying.value) {
        isRelaying.value = false
        relayProgress.value = null
        await useSourcesStore().loadActivity()
      }
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
   * Start checking every fifteen seconds whether the Centrale Canine run of the hour is due, or asked from another
   * device; a hidden window checks about once a minute.
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
    isRelaying,
    relayProgress,
    relay,
    startWatching,
    stopWatching,
  }
})
