import type { CentraleCanineRelayAnswer, RelayedPageResponse, RelayPageRequest } from '~/types/api'
import type {
  CentraleCanineRelayDependencies,
  CentraleCanineRelayPageReading,
  CentraleCanineRelayProgress,
} from '~/types/CentraleCanineRelay'

const MAXIMUM_RELAY_ROUNDS: number = 24
const DELAY_BETWEEN_PAGES_MS: number = 1000
const CLOUDFLARE_REFUSAL_STATUS: number = 403

/** One relay of the Centrale Canine: the API names the pages, the computer reads them, the API runs. */
export class CentraleCanineRelayRunner {
  /**
   * Ask the API which pages to read, read them, and send them back until the API has run every source of the
   * relay; each call carries the pages read since the previous one, the API keeps the rest.
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
    let answer: CentraleCanineRelayAnswer = await dependencies.sendRelayRequest({
      relay_token: null,
      responses: [],
      is_requested_by_user: isRequestedByUser,
    })

    for (let round: number = 1; answer.state === 'pages_needed' && round <= MAXIMUM_RELAY_ROUNDS; round++) {
      const progress: CentraleCanineRelayProgress = {
        source: answer.source ?? null,
        pagesReadCount: 0,
        pagesPlannedCount: answer.page_requests.length,
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
   * Read the pages one per second, in the browser once Cloudflare refused curl, and stop at the first page not read.
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
      if (!this.isPageRead(response)) {
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
}
