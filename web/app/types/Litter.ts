import type { CoatColor, DogSex } from '~/types/api'

export type LitterFilterKey = 'all' | 'preferred' | 'expected'

export type LitterFilterOption = {
  key: LitterFilterKey
  label: string
}

export type LitterSortKey = 'score' | 'distance' | 'price' | 'departure_soonest' | 'departure_latest'

export type LitterSortOption = {
  key: LitterSortKey
  label: string
  description: string
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

export type LitterBrowsingOrigin = 'home' | 'follow-ups'

export type LitterListingLine = {
  key: string
  href: string | null
  label: string
  description: string
  thumbnailUrl: string | null
  isGone: boolean
}

export type LitterPuppyLine = {
  key: string
  href: string | null
  label: string
  sex: DogSex
  sexLabel: string | null
  color: CoatColor | null
  stateLabel: string | null
  isAvailable: boolean
  photoUrl: string | null
  isGone: boolean
}
