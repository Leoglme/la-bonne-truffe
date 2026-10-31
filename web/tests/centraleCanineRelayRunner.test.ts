import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  CentraleCanineRelayState,
  RelayedPageResponse,
  RelayPageRequest,
} from '../app/types/api'
import type { CentraleCanineRelayDependencies, CentraleCanineRelayProgress } from '../app/types/CentraleCanineRelay'
import { describe, expect, it } from 'vitest'
import { CentraleCanineRelayRunner } from '../app/utils/centraleCanineRelayRunner'

type RecordedRelay = {
  sentRequests: CentraleCanineRelayRequest[]
  curlReadUrls: string[]
  browserReadUrls: string[]
  pauseCount: number
}

type ScriptedPageStatuses = {
  curl: Record<string, number>
  browser: Record<string, number>
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
 * Build an empty record of what the runner did.
 *
 * @returns The record.
 */
function emptyRecordedRelay(): RecordedRelay {
  return { sentRequests: [], curlReadUrls: [], browserReadUrls: [], pauseCount: 0 }
}

/**
 * Build dependencies that answer with scripted API answers and page statuses, and record what the runner did.
 *
 * @param apiAnswers - Answers of the API, in order.
 * @param pageStatuses - Status curl and the browser get for a page; 200 when absent.
 * @param recordedRelay - Where the calls are recorded.
 * @returns The dependencies.
 */
function scriptedDependencies(
  apiAnswers: CentraleCanineRelayAnswer[],
  pageStatuses: ScriptedPageStatuses,
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
      recordedRelay.curlReadUrls.push(pageRequest.url)
      return { url: pageRequest.url, status_code: pageStatuses.curl[pageRequest.url] ?? 200, body: '{}' }
    },
    readPageInBrowser: async (pageRequest: RelayPageRequest): Promise<RelayedPageResponse> => {
      recordedRelay.browserReadUrls.push(pageRequest.url)
      return { url: pageRequest.url, status_code: pageStatuses.browser[pageRequest.url] ?? 200, body: '{}' }
    },
    pause: async (): Promise<void> => {
      recordedRelay.pauseCount += 1
    },
  }
}

/**
 * Read the statuses of the pages a relay request carried.
 *
 * @param relayRequest - A request sent to the API.
 * @returns The status of each page, in order.
 */
function statusCodesSentIn(relayRequest: CentraleCanineRelayRequest | undefined): (number | null | undefined)[] {
  return (relayRequest?.responses ?? []).map(
    (response: RelayedPageResponse): number | null | undefined => response.status_code,
  )
}

describe('CentraleCanineRelayRunner', (): void => {
  it('reads the pages the API asks for, round after round, until the run', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    const apiAnswers: CentraleCanineRelayAnswer[] = [
      apiAnswerOf('pages_needed', ['page-0-ille-et-vilaine', 'page-0-morbihan']),
      apiAnswerOf('pages_needed', ['page-1-ille-et-vilaine']),
      apiAnswerOf('run_finished'),
    ]

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
      scriptedDependencies(apiAnswers, { curl: {}, browser: {} }, recordedRelay),
      false,
    )

    expect(lastAnswer.state).toBe('run_finished')
    expect(recordedRelay.curlReadUrls).toEqual(['page-0-ille-et-vilaine', 'page-0-morbihan', 'page-1-ille-et-vilaine'])
    expect(recordedRelay.browserReadUrls).toEqual([])
    expect(recordedRelay.pauseCount).toBe(3)
    expect(
      recordedRelay.sentRequests.map((relayRequest: CentraleCanineRelayRequest): number | undefined => {
        return relayRequest.responses?.length
      }),
    ).toEqual([0, 2, 1])
    expect(recordedRelay.sentRequests[2]?.relay_token).toBe('relay-token')
  })

  it('reads in the browser once Cloudflare refuses curl, until the end of the relay', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    const apiAnswers: CentraleCanineRelayAnswer[] = [
      apiAnswerOf('pages_needed', ['page-0-ille-et-vilaine', 'page-0-morbihan']),
      apiAnswerOf('pages_needed', ['page-1-ille-et-vilaine']),
      apiAnswerOf('run_finished'),
    ]

    await CentraleCanineRelayRunner.relay(
      scriptedDependencies(apiAnswers, { curl: { 'page-0-ille-et-vilaine': 403 }, browser: {} }, recordedRelay),
      false,
    )

    expect(recordedRelay.curlReadUrls).toEqual(['page-0-ille-et-vilaine'])
    expect(recordedRelay.browserReadUrls).toEqual([
      'page-0-ille-et-vilaine',
      'page-0-morbihan',
      'page-1-ille-et-vilaine',
    ])
    expect(statusCodesSentIn(recordedRelay.sentRequests[2])).toEqual([200])
  })

  it('stops at the first page neither curl nor the browser could read, and sends it at once', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    const apiAnswers: CentraleCanineRelayAnswer[] = [
      apiAnswerOf('pages_needed', ['page-0-ille-et-vilaine', 'page-0-morbihan', 'page-0-finistere']),
      apiAnswerOf('run_finished'),
    ]

    await CentraleCanineRelayRunner.relay(
      scriptedDependencies(
        apiAnswers,
        { curl: { 'page-0-morbihan': 403 }, browser: { 'page-0-morbihan': 403 } },
        recordedRelay,
      ),
      false,
    )

    expect(recordedRelay.curlReadUrls).toEqual(['page-0-ille-et-vilaine', 'page-0-morbihan'])
    expect(recordedRelay.browserReadUrls).toEqual(['page-0-morbihan'])
    expect(statusCodesSentIn(recordedRelay.sentRequests[1])).toEqual([200, 403])
  })

  it('reads nothing when the run is not due', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
      scriptedDependencies([apiAnswerOf('not_due')], { curl: {}, browser: {} }, recordedRelay),
      false,
    )

    expect(lastAnswer.state).toBe('not_due')
    expect(recordedRelay.curlReadUrls).toEqual([])
    expect(recordedRelay.sentRequests).toHaveLength(1)
  })

  it('sends a page the computer refuses to read as failed, so that the API ends the run', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    const dependencies: CentraleCanineRelayDependencies = scriptedDependencies(
      [apiAnswerOf('pages_needed', ['page-0-eleveurs', 'page-0-club', 'page-1-eleveurs']), apiAnswerOf('run_finished')],
      { curl: {}, browser: {} },
      recordedRelay,
    )
    dependencies.readPageWithCurl = async (pageRequest: RelayPageRequest): Promise<RelayedPageResponse> => {
      recordedRelay.curlReadUrls.push(pageRequest.url)
      if (pageRequest.url === 'page-0-club') {
        throw 'Adresse refusée : page-0-club'
      }
      return { url: pageRequest.url, status_code: 200, body: '{}' }
    }

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(dependencies, true)

    expect(lastAnswer.state).toBe('run_finished')
    expect(recordedRelay.curlReadUrls).toEqual(['page-0-eleveurs', 'page-0-club'])
    expect(statusCodesSentIn(recordedRelay.sentRequests[1])).toEqual([200, null])
    expect(recordedRelay.sentRequests[1]?.responses?.[1]?.curl_error).toBe('Adresse refusée : page-0-club')
  })

  it('tells where the relay stands after each page', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    const progressReports: CentraleCanineRelayProgress[] = []
    const dependencies: CentraleCanineRelayDependencies = scriptedDependencies(
      [
        { ...apiAnswerOf('pages_needed', ['page-0-eleveurs', 'page-1-eleveurs']), source: 'scc_breeders' },
        apiAnswerOf('run_finished'),
      ],
      { curl: {}, browser: {} },
      recordedRelay,
    )
    dependencies.reportProgress = (progress: CentraleCanineRelayProgress): void => {
      progressReports.push(progress)
    }

    await CentraleCanineRelayRunner.relay(dependencies, false)

    expect(progressReports).toEqual([
      { source: 'scc_breeders', pagesReadCount: 0, pagesPlannedCount: 2, isWaitingForAnotherComputer: false },
      { source: 'scc_breeders', pagesReadCount: 1, pagesPlannedCount: 2, isWaitingForAnotherComputer: false },
      { source: 'scc_breeders', pagesReadCount: 2, pagesPlannedCount: 2, isWaitingForAnotherComputer: false },
    ])
  })

  it('waits for another computer to finish, then relays, when the user asked', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    const progressReports: CentraleCanineRelayProgress[] = []
    const dependencies: CentraleCanineRelayDependencies = scriptedDependencies(
      [apiAnswerOf('busy'), apiAnswerOf('busy'), apiAnswerOf('pages_needed', ['page-0']), apiAnswerOf('run_finished')],
      { curl: {}, browser: {} },
      recordedRelay,
    )
    dependencies.reportProgress = (progress: CentraleCanineRelayProgress): void => {
      progressReports.push(progress)
    }

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(dependencies, true)

    expect(lastAnswer.state).toBe('run_finished')
    expect(recordedRelay.sentRequests).toHaveLength(4)
    expect(recordedRelay.pauseCount).toBe(3)
    expect(progressReports[0]?.isWaitingForAnotherComputer).toBe(true)
  })

  it('does not wait for another computer when the check is a routine one', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(
      scriptedDependencies([apiAnswerOf('busy')], { curl: {}, browser: {} }, recordedRelay),
      false,
    )

    expect(lastAnswer.state).toBe('busy')
    expect(recordedRelay.sentRequests).toHaveLength(1)
  })

  it('gives up waiting after ten minutes and leaves the request to the API', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    let clock: number = 0
    const dependencies: CentraleCanineRelayDependencies = scriptedDependencies(
      [apiAnswerOf('busy'), apiAnswerOf('busy'), apiAnswerOf('busy')],
      { curl: {}, browser: {} },
      recordedRelay,
    )
    dependencies.now = (): number => clock
    dependencies.pause = async (): Promise<void> => {
      clock += 5 * 60_000
    }

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(dependencies, true)

    expect(lastAnswer.state).toBe('busy')
    expect(recordedRelay.sentRequests).toHaveLength(3)
  })

  it('sends the pages read so far after forty seconds, and goes on with the rest', async (): Promise<void> => {
    const recordedRelay: RecordedRelay = emptyRecordedRelay()
    let clock: number = 0
    const dependencies: CentraleCanineRelayDependencies = scriptedDependencies(
      [
        apiAnswerOf('pages_needed', ['page-0', 'page-1', 'page-2']),
        apiAnswerOf('pages_needed', ['page-2']),
        apiAnswerOf('run_finished'),
      ],
      { curl: {}, browser: {} },
      recordedRelay,
    )
    dependencies.now = (): number => clock
    dependencies.pause = async (): Promise<void> => {
      clock += 25_000
    }

    const lastAnswer: CentraleCanineRelayAnswer = await CentraleCanineRelayRunner.relay(dependencies, false)

    expect(lastAnswer.state).toBe('run_finished')
    expect(recordedRelay.curlReadUrls).toEqual(['page-0', 'page-1', 'page-2'])
    expect(
      recordedRelay.sentRequests.map((relayRequest: CentraleCanineRelayRequest): number | undefined => {
        return relayRequest.responses?.length
      }),
    ).toEqual([0, 2, 1])
  })
})
