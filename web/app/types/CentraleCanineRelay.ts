import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  ListingSource,
  RelayedPageResponse,
  RelayPageRequest,
} from '~/types/api'

/**
 * Where a relay stands on this computer: the source being read and the pages read so far in this round, or
 * the wait for another computer to finish its own relay.
 */
export type CentraleCanineRelayProgress = {
  source: ListingSource | null
  pagesReadCount: number
  pagesPlannedCount: number
  isWaitingForAnotherComputer: boolean
}

export type CentraleCanineRelayDependencies = {
  sendRelayRequest: (relayRequest: CentraleCanineRelayRequest) => Promise<CentraleCanineRelayAnswer>
  readPageWithCurl: (pageRequest: RelayPageRequest) => Promise<RelayedPageResponse>
  readPageInBrowser: (pageRequest: RelayPageRequest) => Promise<RelayedPageResponse>
  pause: (milliseconds: number) => Promise<void>
  reportProgress?: (progress: CentraleCanineRelayProgress) => void
  now?: () => number
}

export type CentraleCanineRelayPageReading = {
  responses: RelayedPageResponse[]
  isCurlRefused: boolean
}
