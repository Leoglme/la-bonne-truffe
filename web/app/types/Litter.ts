export type LitterFilterKey = 'all' | 'preferred' | 'expected'

export type LitterFilterOption = {
  key: LitterFilterKey
  label: string
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

export type LitterBrowsingOrigin = 'home' | 'follow-ups'

export type LitterListingLine = {
  key: string
  href: string | null
  label: string
  description: string
  thumbnailUrl: string | null
}
