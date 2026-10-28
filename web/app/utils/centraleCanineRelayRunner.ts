import type { CentraleCanineRelayAnswer, RelayedPageResponse, RelayPageRequest } from '~/types/api'
import type { CentraleCanineRelayDependencies } from '~/types/CentraleCanineRelay'

const MAXIMUM_RELAY_ROUNDS: number = 6
const DELAY_BETWEEN_PAGES_MS: number = 1000

/** One relay of the Centrale Canine: the API names the pages, the curl of Windows reads them, the API runs. */
export class CentraleCanineRelayRunner {
  /**
   * Ask the API which pages to read, read them, and send them back until the API has run the collection.
   *
   * @param dependencies - How to reach the API, read a page with curl and pause between two pages.
   * @param isRequestedByUser - « Relever maintenant »: run even when the last run is recent.
   * @returns The last answer of the API.
   */
  static async relay(
    dependencies: CentraleCanineRelayDependencies,
    isRequestedByUser: boolean,
  ): Promise<CentraleCanineRelayAnswer> {
    let relayedResponses: RelayedPageResponse[] = []
    let answer: CentraleCanineRelayAnswer = await dependencies.sendRelayRequest({
      relay_token: null,
      responses: [],
      is_requested_by_user: isRequestedByUser,
    })

    for (let round: number = 1; answer.state === 'pages_needed' && round <= MAXIMUM_RELAY_ROUNDS; round++) {
      const roundResponses: RelayedPageResponse[] = await this.readPages(dependencies, answer.page_requests)
      relayedResponses = [...relayedResponses, ...roundResponses]
      answer = await dependencies.sendRelayRequest({
        relay_token: answer.relay_token,
        responses: relayedResponses,
        is_requested_by_user: isRequestedByUser,
      })
    }
    return answer
  }

  /**
   * Read the pages one per second, and stop at the first one curl did not get: insisting gets the connection challenged.
   *
   * @param dependencies - How to read a page with curl and pause between two pages.
   * @param pageRequests - Pages the API asked for, in the order the collector reads them.
   * @returns The pages read, the failed one last.
   */
  private static async readPages(
    dependencies: CentraleCanineRelayDependencies,
    pageRequests: RelayPageRequest[],
  ): Promise<RelayedPageResponse[]> {
    const responses: RelayedPageResponse[] = []
    for (const pageRequest of pageRequests) {
      await dependencies.pause(DELAY_BETWEEN_PAGES_MS)
      const response: RelayedPageResponse = await dependencies.readPageWithCurl(pageRequest)
      responses.push(response)
      if (!this.isPageRead(response)) {
        break
      }
    }
    return responses
  }

  /**
   * Whether curl got the page itself, and not an error or a refusal.
   *
   * @param response - The page as curl received it.
   * @returns True for a 2xx status.
   */
  private static isPageRead(response: RelayedPageResponse): boolean {
    const statusCode: number | null | undefined = response.status_code
    return typeof statusCode === 'number' && statusCode >= 200 && statusCode < 300
  }
}
