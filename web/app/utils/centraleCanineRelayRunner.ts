import type { CentraleCanineRelayAnswer, RelayedPageResponse, RelayPageRequest } from '~/types/api'
import type { CentraleCanineRelayDependencies, CentraleCanineRelayPageReading } from '~/types/CentraleCanineRelay'

const MAXIMUM_RELAY_ROUNDS: number = 6
const DELAY_BETWEEN_PAGES_MS: number = 1000
const CLOUDFLARE_REFUSAL_STATUS: number = 403

/** One relay of the Centrale Canine: the API names the pages, the computer reads them, the API runs. */
export class CentraleCanineRelayRunner {
  /**
   * Ask the API which pages to read, read them, and send them back until the API has run the collection.
   *
   * @param dependencies - How to reach the API, read a page with curl or in the browser, and pause between two pages.
   * @param isRequestedByUser - « Relever maintenant »: run even when the last run is recent.
   * @returns The last answer of the API.
   */
  static async relay(
    dependencies: CentraleCanineRelayDependencies,
    isRequestedByUser: boolean,
  ): Promise<CentraleCanineRelayAnswer> {
    let relayedResponses: RelayedPageResponse[] = []
    let isCurlRefused: boolean = false
    let answer: CentraleCanineRelayAnswer = await dependencies.sendRelayRequest({
      relay_token: null,
      responses: [],
      is_requested_by_user: isRequestedByUser,
    })

    for (let round: number = 1; answer.state === 'pages_needed' && round <= MAXIMUM_RELAY_ROUNDS; round++) {
      const pageReading: CentraleCanineRelayPageReading = await this.readPages(
        dependencies,
        answer.page_requests,
        isCurlRefused,
      )
      isCurlRefused = pageReading.isCurlRefused
      relayedResponses = [...relayedResponses, ...pageReading.responses]
      answer = await dependencies.sendRelayRequest({
        relay_token: answer.relay_token,
        responses: relayedResponses,
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
   * @returns The pages read, the failed one last, and whether Cloudflare refused curl.
   */
  private static async readPages(
    dependencies: CentraleCanineRelayDependencies,
    pageRequests: RelayPageRequest[],
    isCurlRefusedAtStart: boolean,
  ): Promise<CentraleCanineRelayPageReading> {
    const responses: RelayedPageResponse[] = []
    let isCurlRefused: boolean = isCurlRefusedAtStart
    for (const pageRequest of pageRequests) {
      await dependencies.pause(DELAY_BETWEEN_PAGES_MS)
      let response: RelayedPageResponse = await this.readPage(dependencies, pageRequest, isCurlRefused)
      if (!isCurlRefused && response.status_code === CLOUDFLARE_REFUSAL_STATUS) {
        isCurlRefused = true
        response = await dependencies.readPageInBrowser(pageRequest)
      }
      responses.push(response)
      if (!this.isPageRead(response)) {
        break
      }
    }
    return { responses, isCurlRefused }
  }

  /**
   * Read one page with curl, or in the browser once Cloudflare refused curl during this relay.
   *
   * @param dependencies - How to read a page.
   * @param pageRequest - The page to read.
   * @param isCurlRefused - Whether Cloudflare already refused curl during this relay.
   * @returns The page as read.
   */
  private static readPage(
    dependencies: CentraleCanineRelayDependencies,
    pageRequest: RelayPageRequest,
    isCurlRefused: boolean,
  ): Promise<RelayedPageResponse> {
    if (isCurlRefused) {
      return dependencies.readPageInBrowser(pageRequest)
    }
    return dependencies.readPageWithCurl(pageRequest)
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
