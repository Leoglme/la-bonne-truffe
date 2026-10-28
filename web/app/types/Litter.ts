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

export type LitterDayFactKey = 'birth' | 'departure'

export type LitterDayFact = {
  key: LitterDayFactKey
  label: string
  value: string
  compactValue: string
}

export type LitterPuppiesFact = {
  key: 'puppies'
  label: string
}

export type LitterKeyFact = LitterDayFact | LitterPuppiesFact

export type LitterPrimaryAction = {
  href: string
  label: string
  isCall: boolean
}
