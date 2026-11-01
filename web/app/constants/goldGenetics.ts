import type { FrenchGender } from '~/types/FrenchText'
import type { GoldGenotype } from '~/types/GoldGenetics'

/** What a dog carries of the gold, by its E locus genotype, agreed with its sex. */
export const GOLD_GENOTYPE_LABELS: Record<GoldGenotype, Record<FrenchGender, string>> = {
  'e/e': { masculine: 'testé gold (e/e)', feminine: 'testée gold (e/e)' },
  'E/e': { masculine: 'porteur du gold (E/e)', feminine: 'porteuse du gold (E/e)' },
  'E/E': { masculine: 'ne porte pas le gold (E/E)', feminine: 'ne porte pas le gold (E/E)' },
}

export const GOLD_ONLY_TRANSMISSION_LABELS: Record<FrenchGender, string> = {
  masculine: 'il ne transmet que le gold',
  feminine: 'elle ne transmet que le gold',
}

export const TESTED_GENOTYPE_SOURCE_LABEL: string = 'd’après son test ADN'
export const PARENTS_GENOTYPE_SOURCE_LABEL: string = 'd’après ses parents'
