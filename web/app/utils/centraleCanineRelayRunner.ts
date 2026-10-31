import type { CentraleCanineRelayAnswer, RelayedPageResponse, RelayPageRequest } from '~/types/api'
import type {
  CentraleCanineRelayDependencies,
  CentraleCanineRelayPageReading,
  CentraleCanineRelayProgress,
} from '~/types/CentraleCanineRelay'

const MAXIMUM_RELAY_ROUNDS: number = 60
const DELAY_BETWEEN_PAGES_MS: number = 1000
const CLOUDFLARE_REFUSAL_STATUS: number = 403
const SEND_PAGES_AFTER_MS: number = 40_000
const BUSY_RETRY_DELAY_MS: number = 15_000
const MAXIMUM_BUSY_WAIT_MS: number = 10 * 60_000

/** One relay of the Centrale Canine: the API names the pages, the computer reads them, the API runs. */
export class CentraleCanineRelayRunner {
  /**
   * Ask the API which pages to read, read them, and send them back until the API has run every source of the
   * relay. The pages read are sent at least every forty seconds, so that the API knows the relay is alive and
   * the screen shows it move; a relay asked by the user waits for another computer to finish its own.
   *
   * @param dependencies - How to reach the API, read a page with curl or in the browser, and pause between two pages.
   * @param isRequestedByUser - « Relever maintenant »: every source runs, even when its last run is recent.
   * @returns The last answer of the API.
   */
  static async relay(
    dependencies: CentraleCanineRelayDependencies,
    isRequestedByUser: boolean,
  ): Promise<CentraleCanineRelayAnswer> {
    let isCurlRefused: boolean = false
    let answer: CentraleCanineRelayAnswer = await this.start(dependencies, isRequestedByUser)

    for (let round: number = 1; answer.state === 'pages_needed' && round <= MAXIMUM_RELAY_ROUNDS; round++) {
      const progress: CentraleCanineRelayProgress = {
        source: answer.source ?? null,
        pagesReadCount: 0,
        pagesPlannedCount: answer.page_requests.length,
        isWaitingForAnotherComputer: false,
      }
      dependencies.reportProgress?.(progress)
      const pageReading: CentraleCanineRelayPageReading = await this.readPages(
        dependencies,
        answer.page_requests,
        isCurlRefused,
        progress,
      )
      isCurlRefused = pageReading.isCurlRefused
      answer = await dependencies.sendRelayRequest({
        relay_token: answer.relay_token,
        responses: pageReading.responses,
        is_requested_by_user: isRequestedByUser,
      })
    }
    return answer
  }

  /**
   * Open the relay; when another computer holds it and the user asked, try again every fifteen seconds for
   * up to ten minutes, telling the screen about the wait.
   *
   * @param dependencies - How to reach the API and pause.
   * @param isRequestedByUser - Whether the user asked, which is worth waiting for.
   * @returns The first answer that is not « busy », or the last « busy » once the wait is over.
   */
  private static async start(
    dependencies: CentraleCanineRelayDependencies,
    isRequestedByUser: boolean,
  ): Promise<CentraleCanineRelayAnswer> {
    const startedAt: number = this.readClock(dependencies)
    let answer: CentraleCanineRelayAnswer = await dependencies.sendRelayRequest({
      relay_token: null,
      responses: [],
      is_requested_by_user: isRequestedByUser,
    })
    while (
      answer.state === 'busy' &&
      isRequestedByUser &&
      this.readClock(dependencies) - startedAt < MAXIMUM_BUSY_WAIT_MS
    ) {
      dependencies.reportProgress?.({
        source: null,
        pagesReadCount: 0,
        pagesPlannedCount: 0,
        isWaitingForAnotherComputer: true,
      })
      await dependencies.pause(BUSY_RETRY_DELAY_MS)
      answer = await dependencies.sendRelayRequest({
        relay_token: null,
        responses: [],
        is_requested_by_user: isRequestedByUser,
      })
    }
    return answer
  }

  /**
   * Read the pages one per second, in the browser once Cloudflare refused curl, and stop at the first page not
   * read or once forty seconds have passed: the pages read so far are sent, the API asks for the rest.
   *
   * @param dependencies - How to read a page and pause between two pages.
   * @param pageRequests - Pages the API asked for, in the order the collector reads them.
   * @param isCurlRefusedAtStart - Whether Cloudflare already refused curl during this relay.
   * @param progress - The progress of the round, told after each page.
   * @returns The pages read, the failed one last, and whether Cloudflare refused curl.
   */
  private static async readPages(
    dependencies: CentraleCanineRelayDependencies,
    pageRequests: RelayPageRequest[],
    isCurlRefusedAtStart: boolean,
    progress: CentraleCanineRelayProgress,
  ): Promise<CentraleCanineRelayPageReading> {
    const startedAt: number = this.readClock(dependencies)
    const responses: RelayedPageResponse[] = []
    let isCurlRefused: boolean = isCurlRefusedAtStart
    for (const pageRequest of pageRequests) {
      await dependencies.pause(DELAY_BETWEEN_PAGES_MS)
      let response: RelayedPageResponse = await this.readPage(dependencies, pageRequest, isCurlRefused)
      if (!isCurlRefused && response.status_code === CLOUDFLARE_REFUSAL_STATUS) {
        isCurlRefused = true
        response = await this.readPage(dependencies, pageRequest, isCurlRefused)
      }
      responses.push(response)
      dependencies.reportProgress?.({ ...progress, pagesReadCount: responses.length })
      if (!this.isPageRead(response) || this.readClock(dependencies) - startedAt >= SEND_PAGES_AFTER_MS) {
        break
      }
    }
    return { responses, isCurlRefused }
  }

  /**
   * Read one page with curl, or in the browser once Cloudflare refused curl during this relay; a page the
   * computer refuses to read is sent to the API as failed, so that the run fails instead of hanging.
   *
   * @param dependencies - How to read a page.
   * @param pageRequest - The page to read.
   * @param isCurlRefused - Whether Cloudflare already refused curl during this relay.
   * @returns The page as read, or why it could not be.
   */
  private static async readPage(
    dependencies: CentraleCanineRelayDependencies,
    pageRequest: RelayPageRequest,
    isCurlRefused: boolean,
  ): Promise<RelayedPageResponse> {
    try {
      return isCurlRefused
        ? await dependencies.readPageInBrowser(pageRequest)
        : await dependencies.readPageWithCurl(pageRequest)
    } catch (error: unknown) {
      return {
        url: pageRequest.url,
        status_code: null,
        body: '',
        curl_error: error instanceof Error ? error.message : String(error),
      }
    }
  }

  /**
   * Whether the page itself was read, and not an error or a refusal.
   *
   * @param response - The page as read.
   * @returns True for a 2xx status.
   */
  private static isPageRead(response: RelayedPageResponse): boolean {
    const statusCode: number | null | undefined = response.status_code
    return typeof statusCode === 'number' && statusCode >= 200 && statusCode < 300
  }

  /**
   * The time, from the clock of the dependencies when the tests give one.
   *
   * @param dependencies - The dependencies.
   * @returns Milliseconds.
   */
  private static readClock(dependencies: CentraleCanineRelayDependencies): number {
    return dependencies.now?.() ?? Date.now()
  }
}
