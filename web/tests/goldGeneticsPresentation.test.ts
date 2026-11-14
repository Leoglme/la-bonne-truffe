import type { LitterDetail, LitterParent } from '../app/types/api'
import { describe, expect, it } from 'vitest'
import { GoldGeneticsPresentation } from '../app/utils/goldGeneticsPresentation'

const GOLD_TESTED_SIRE: LitterParent = {
  name: 'Père de test 11',
  rating: 1,
  color: 'gold',
  color_code: 'F.Or.',
  e_locus: 'e/e',
  carries_gold_by_parents: false,
  health_codes: ['LocE-e/e', 'PRCD-1.1'],
  scc_url: null,
  photo_url: null,
}

const CARRIER_TESTED_DAM: LitterParent = {
  name: 'Mère de test 12',
  rating: 1,
  color: 'bleu_rouan',
  color_code: 'Noi. Bla.Rou.',
  e_locus: 'E/e',
  carries_gold_by_parents: false,
  health_codes: ['LocEm-Em/e'],
  scc_url: null,
  photo_url: null,
}

const LITTER: LitterDetail = {
  id: 3,
  name: 'Du Clos de l’Élevage A',
  place: 'Évron',
  town: 'Évron',
  department_code: '53',
  department_name: 'Mayenne',
  breeder_latitude: null,
  breeder_longitude: null,
  kind: 'litter_born',
  tier: 'acceptable',
  score: 57,
  colors: [{ color: 'gold', confidence: 'ambiguous' }],
  lof_status: 'lof',
  male_count: 1,
  female_count: 2,
  has_confirmed_sexes: false,
  puppies_available: 2,
  price_cents: null,
  birth_date: '2026-10-29',
  expected_birth_date: null,
  available_from: '2026-12-24',
  photo_url: null,
  first_seen_at: '2026-10-30T09:00:00',
  latest_listing_appeared_at: '2026-10-30T09:00:00',
  last_seen_at: '2026-11-01T06:40:00',
  is_active: true,
  sources: ['centrale_canine', 'chiens_de_france_sites'],
  follow_up_status: null,
  genetic_screening: null,
  gold_puppy_odds: 0.5,
  reasons: [],
  flags: [],
  litter_number: null,
  mating_date: null,
  sire: GOLD_TESTED_SIRE,
  dam: CARRIER_TESTED_DAM,
  breeder: null,
  photos: [],
  listings: [],
  follow_up: null,
}

describe('GoldGeneticsPresentation.buildGenotypeLabel', (): void => {
  it('words a tested genotype, agreed with the sex', (): void => {
    expect(GoldGeneticsPresentation.buildGenotypeLabel(GOLD_TESTED_SIRE, 'masculine')).toBe('testé gold (e/e)')
    expect(GoldGeneticsPresentation.buildGenotypeLabel(CARRIER_TESTED_DAM, 'feminine')).toBe('porteuse du gold (E/e)')
    expect(
      GoldGeneticsPresentation.buildGenotypeLabel({ e_locus: 'E/E', carries_gold_by_parents: false }, 'feminine'),
    ).toBe('ne porte pas le gold (E/E)')
  })

  it('says when the carrier is told by a gold parent, and nothing while unknown', (): void => {
    expect(
      GoldGeneticsPresentation.buildGenotypeLabel(
        { color: 'bleu_rouan', e_locus: null, carries_gold_by_parents: true },
        'feminine',
      ),
    ).toBe('porteuse du gold (E/e), d’après ses parents')
    expect(
      GoldGeneticsPresentation.buildGenotypeLabel(
        { color: 'gold', e_locus: null, carries_gold_by_parents: false },
        'masculine',
      ),
    ).toBeNull()
  })
})

describe('GoldGeneticsPresentation.buildGenotypeExplanation', (): void => {
  it('tells what a tested parent gives, or how its genotype is known', (): void => {
    expect(GoldGeneticsPresentation.buildGenotypeExplanation(GOLD_TESTED_SIRE, 'masculine')).toBe(
      'testé gold (e/e) : il ne transmet que le gold',
    )
    expect(GoldGeneticsPresentation.buildGenotypeExplanation(CARRIER_TESTED_DAM, 'feminine')).toBe(
      'porteuse du gold (E/e), d’après son test ADN',
    )
    expect(
      GoldGeneticsPresentation.buildGenotypeExplanation(
        { color: 'noir', e_locus: null, carries_gold_by_parents: true },
        'masculine',
      ),
    ).toBe('porteur du gold (E/e), d’après ses parents')
  })
})

describe('GoldGeneticsPresentation.isEveryPuppyGold', (): void => {
  it('tells a litter whose parents only give the gold', (): void => {
    expect(GoldGeneticsPresentation.isEveryPuppyGold(1)).toBe(true)
    expect(GoldGeneticsPresentation.isEveryPuppyGold(0.5)).toBe(false)
    expect(GoldGeneticsPresentation.isEveryPuppyGold(null)).toBe(false)
  })
})

describe('GoldGeneticsPresentation.buildPuppyOddsLine', (): void => {
  it('words the odds when only some puppies can be gold', (): void => {
    expect(GoldGeneticsPresentation.buildPuppyOddsLine(0.5)).toBe('Gold possible : un chiot sur deux')
    expect(GoldGeneticsPresentation.buildPuppyOddsLine(0.25)).toBe('Gold possible : un chiot sur quatre')
    expect(GoldGeneticsPresentation.buildPuppyOddsLine(1)).toBeNull()
    expect(GoldGeneticsPresentation.buildPuppyOddsLine(null)).toBeNull()
  })
})

describe('GoldGeneticsPresentation.buildPuppyOddsSummary', (): void => {
  it('names the parent that gives the gold, then the odds of one gold among the puppies born', (): void => {
    expect(GoldGeneticsPresentation.buildPuppyOddsSummary(LITTER)).toEqual({
      figure: '1 sur 2',
      figureCaption: 'par chiot',
      explanation:
        'Le père ne transmet que le gold et la mère le porte : chaque chiot a une chance sur deux d’être gold. ' +
        'Au moins un gold sur les trois, 7 fois sur 8.',
      isGoldRuledOut: false,
    })
  })

  it('reads a gold coat and a carrier told by the parents, and turns long odds into a share of 100', (): void => {
    expect(
      GoldGeneticsPresentation.buildPuppyOddsSummary({
        ...LITTER,
        male_count: 2,
        female_count: 3,
        sire: { ...GOLD_TESTED_SIRE, color: 'noir', e_locus: null, carries_gold_by_parents: true },
        dam: { ...CARRIER_TESTED_DAM, color: 'gold', e_locus: null },
      })?.explanation,
    ).toBe(
      'La mère ne transmet que le gold et le père le porte : chaque chiot a une chance sur deux d’être gold. ' +
        'Au moins un gold sur les cinq, 97 fois sur 100.',
    )
  })

  it('explains two carriers, a gold couple, and odds whose parents are not both known', (): void => {
    expect(
      GoldGeneticsPresentation.buildPuppyOddsSummary({
        ...LITTER,
        gold_puppy_odds: 0.25,
        male_count: 1,
        female_count: 1,
        sire: { ...GOLD_TESTED_SIRE, color: 'noir', e_locus: 'E/e' },
      }),
    ).toEqual({
      figure: '1 sur 4',
      figureCaption: 'par chiot',
      explanation:
        'Le père et la mère portent le gold sans être gold : chaque chiot a une chance sur quatre d’être gold. ' +
        'Au moins un gold sur les deux, 7 fois sur 16.',
      isGoldRuledOut: false,
    })
    expect(GoldGeneticsPresentation.buildPuppyOddsSummary({ ...LITTER, gold_puppy_odds: 1 })).toEqual({
      figure: 'Tous',
      figureCaption: 'gold',
      explanation: 'Le père et la mère sont gold : tous les chiots seront gold.',
      isGoldRuledOut: false,
    })
    expect(
      GoldGeneticsPresentation.buildPuppyOddsSummary({
        ...LITTER,
        kind: 'litter_expected',
        male_count: null,
        female_count: null,
        sire: null,
      })?.explanation,
    ).toBe('Chaque chiot a une chance sur deux d’être gold.')
    expect(GoldGeneticsPresentation.buildPuppyOddsSummary({ ...LITTER, gold_puppy_odds: null })).toBeNull()
  })

  it('says « Aucun gold » with the reason when the parents rule it out, unless a source announces gold', (): void => {
    const reason: string = 'La mère, testée E/E, ne transmet pas le gold : aucun chiot ne sera gold.'
    const ruledOut: LitterDetail = {
      ...LITTER,
      gold_puppy_odds: null,
      gold_exclusion_reason: reason,
      colors: [{ color: 'noir', confidence: 'ambiguous' }],
    }

    expect(GoldGeneticsPresentation.buildPuppyOddsSummary(ruledOut)).toEqual({
      figure: 'Aucun',
      figureCaption: 'gold',
      explanation: reason,
      isGoldRuledOut: true,
    })
    expect(
      GoldGeneticsPresentation.buildPuppyOddsSummary({
        ...ruledOut,
        colors: [{ color: 'gold', confidence: 'certain' }],
      }),
    ).toBeNull()
  })
})
