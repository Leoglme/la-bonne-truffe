import type {
  CentraleCanineRelayAnswer,
  CentraleCanineRelayRequest,
  RelayedPageResponse,
  RelayPageRequest,
} from '~/types/api'

export type CentraleCanineRelayDependencies = {
  sendRelayRequest: (relayRequest: CentraleCanineRelayRequest) => Promise<CentraleCanineRelayAnswer>
  readPageWithCurl: (pageRequest: RelayPageRequest) => Promise<RelayedPageResponse>
  pause: (milliseconds: number) => Promise<void>
}
