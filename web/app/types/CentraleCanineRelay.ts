import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  ListingSource,
  RelayedPageResponse,
  RelayPageRequest,
} from '~/types/api'

/** Where a relay stands on this computer: the source being read, and the pages read so far in this round. */
export type CentraleCanineRelayProgress = {
  source: ListingSource | null
  pagesReadCount: number
  pagesPlannedCount: number
}

export type CentraleCanineRelayDependencies = {
  sendRelayRequest: (relayRequest: CentraleCanineRelayRequest) => Promise<CentraleCanineRelayAnswer>
  readPageWithCurl: (pageRequest: RelayPageRequest) => Promise<RelayedPageResponse>
  readPageInBrowser: (pageRequest: RelayPageRequest) => Promise<RelayedPageResponse>
  pause: (milliseconds: number) => Promise<void>
  reportProgress?: (progress: CentraleCanineRelayProgress) => void
}

export type CentraleCanineRelayPageReading = {
  responses: RelayedPageResponse[]
  isCurlRefused: boolean
}
