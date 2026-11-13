import type { ListingSource, SourceActivity, SourceStatus } from '~/types/api'
import type { CentraleCanineRelayProgress } from '~/types/CentraleCanineRelay'

export type SourceRunPhase =
  | 'idle'
  | 'running_on_server'
  | 'relaying_here'
  | 'relaying_elsewhere'
  | 'waiting_for_computer'
  | 'waiting_for_computer_to_turn_on'

export type SourceRunContext = {
  activity: SourceActivity | null
  isDesktopApp: boolean
  isRelayingHere: boolean
  relayProgressHere: CentraleCanineRelayProgress | null
}

export type SourceRunButton = {
  label: string
  isLoading: boolean
  isDisabled: boolean
}

export type SourceRunCard = {
  status: SourceStatus
  phase: SourceRunPhase
  button: SourceRunButton
  activityLine: string | null
}

export type AskedSourceRun = {
  source: ListingSource
  isRelayed: boolean
  lastRunTimesBefore: Record<string, string | null>
}

export type SourceRunEndNotice = {
  title: string
  color: 'success' | 'error' | 'neutral'
}

export type SourceRunCountForms = {
  singularForm: string
  pluralForm: string
}
