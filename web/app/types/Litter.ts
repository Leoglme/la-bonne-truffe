import type { ListingKind, MatchTier } from '~/types/api'

export type LitterFilterKey = 'all' | 'preferred' | 'expected'

export type LitterFilterOption = {
  key: LitterFilterKey
  label: string
}

export type LitterListFilters = {
  tier?: MatchTier
  kind?: ListingKind
}

export type LitterKeyFact = {
  label: string
  value: string
  compactValue: string
}

export type LitterPrimaryAction = {
  href: string
  label: string
  isCall: boolean
}
