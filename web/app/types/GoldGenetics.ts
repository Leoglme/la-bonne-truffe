import type { CoatColor } from '~/types/api'

export type GoldGenotype = 'e/e' | 'E/e' | 'E/E'

export type GoldGenotypeFacts = {
  color?: CoatColor | null
  e_locus?: string | null
  carries_gold_by_parents: boolean
}

export type GoldPuppyOddsSummary = {
  figure: string
  figureCaption: string
  explanation: string
  isGoldRuledOut: boolean
}
