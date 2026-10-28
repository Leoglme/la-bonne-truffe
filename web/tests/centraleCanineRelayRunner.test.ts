import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  CentraleCanineRelayState,
  RelayedPageResponse,
  RelayPageRequest,
} from '../app/types/api'
import type { CentraleCanineRelayDependencies } from '../app/types/CentraleCanineRelay'
import { describe, expect, it } from 'vitest'
import { CentraleCanineRelayRunner } from '../app/utils/centraleCanineRelayRunner'

type RecordedRelay = {
  sentRequests: CentraleCanineRelayRequest[]
  readUrls: string[]
  pauseCount: number
}

const PAGE_HEADERS: Record<string, string> = { 'User-Agent': 'Mozilla/5.0', Accept: 'application/json' }

/**
 * Build an answer of the API.
 *
 * @param state - What the desktop app does next.
 * @param pageUrls - Pages the API asks for.
 * @returns The answer.
 */
function apiAnswerOf(state: CentraleCanineRelayState, pageUrls: string[] = []): CentraleCanineRelayAnswer {
  return {
    state,
    relay_token: state === 'pages_needed' ? 'relay-token' : null,
    page_requests: pageUrls.map((url: string): RelayPageRequest => ({ url, headers: PAGE_HEADERS })),
    source_statuses: [],
  }
}

/**
 * Build dependencies that answer with scripted API answers and page statuses, and record what the runner did.
 *
 * @param apiAnswers - Answers of the API, in order.
 * @param statusCodeByUrl - Status curl gets for a page; 200 when absent.
 * @param recordedRelay - Where the calls are recorded.
 * @returns The dependencies.
 */
function scriptedDependencies(
  apiAnswers: CentraleCanineRelayAnswer[],
  statusCodeByUrl: Record<string, number>,
  recordedRelay: RecordedRelay,
): CentraleCanineRelayDependencies {
  return {
    sendRelayRequest: async (relayRequest: CentraleCanineRelayRequest): Promise<CentraleCanineRelayAnswer> => {
      recordedRelay.sentRequests.push(relayRequest)
      const nextAnswer: CentraleCanineRelayAnswer | undefined = apiAnswers.shift()
      if (!nextAnswer) {
        throw new Error('No scripted answer left')
      }
      return nextAnswer
    },
    readPageWithCurl: async (pageRequest: RelayPageRequest): Promise<RelayedPageResponse> => {
      recordedRelay.readUrls.push(pageRequest.url)
      return { url: pageRequest.url, status_code: statusCodeByUrl[pageRequest.url] ?? 200, body: '{}' }
    },
    pause: async (): Promise<void> => {
      recordedRelay.pauseCount += 1
    },
  }
}

describe('CentraleCanineRelayRunner', (): void => {
  it('reads the pages the API asks for, round after round, until the run', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = { sentRequests: [], readUrls: [], pauseCount: 0 }
    const apiAnswers: CentraleCanineRelayAnswer[] = [
      apiAnswerOf('pages_needed', ['page-0-ille-et-vilaine', 'page-0-morbihan']),
      apiAnswerOf('pages_needed', ['page-1-ille-et-vilaine']),
      apiAnswerOf('run_finished'),
    ]

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
      scriptedDependencies(apiAnswers, {}, recordedRelay),
      false,
    )

    expect(lastAnswer.state).toBe('run_finished')
    expect(recordedRelay.readUrls).toEqual(['page-0-ille-et-vilaine', 'page-0-morbihan', 'page-1-ille-et-vilaine'])
    expect(recordedRelay.pauseCount).toBe(3)
    expect(
      recordedRelay.sentRequests.map((relayRequest: CentraleCanineRelayRequest): number | undefined => {
        return relayRequest.responses?.length
      }),
    ).toEqual([0, 2, 3])
    expect(recordedRelay.sentRequests[2]?.relay_token).toBe('relay-token')
  })

  it('stops at the first refused page and sends it at once', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = { sentRequests: [], readUrls: [], pauseCount: 0 }
    const apiAnswers: CentraleCanineRelayAnswer[] = [
      apiAnswerOf('pages_needed', ['page-0-ille-et-vilaine', 'page-0-morbihan', 'page-0-finistere']),
      apiAnswerOf('run_finished'),
    ]

    await CentraleCanineRelayRunner.relay(
      scriptedDependencies(apiAnswers, { 'page-0-morbihan': 403 }, recordedRelay),
      false,
    )

    expect(recordedRelay.readUrls).toEqual(['page-0-ille-et-vilaine', 'page-0-morbihan'])
    expect(
      recordedRelay.sentRequests[1]?.responses?.map(
        (response: RelayedPageResponse): number | null | undefined => response.status_code,
      ),
    ).toEqual([200, 403])
  })

  it('reads nothing when the run is not due', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = { sentRequests: [], readUrls: [], pauseCount: 0 }

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
      scriptedDependencies([apiAnswerOf('not_due')], {}, recordedRelay),
      false,
    )

    expect(lastAnswer.state).toBe('not_due')
    expect(recordedRelay.readUrls).toEqual([])
    expect(recordedRelay.sentRequests).toHaveLength(1)
  })
})
