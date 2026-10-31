import type { LitterCard } from '../app/types/api'
import { describe, expect, it } from 'vitest'
import { LitterPresentation } from '../app/utils/litterPresentation'

const BORN_GOLD_LITTER: LitterCard = {
  id: 1,
  name: 'De Kerlann',
  place: 'Redon',
  town: 'Redon',
  department_code: '35',
  department_name: 'Ille-et-Vilaine',
  breeder_latitude: null,
  breeder_longitude: null,
  kind: 'litter_born',
  tier: 'preferred',
  score: 96,
  colors: [{ color: 'gold', confidence: 'certain' }],
  lof_status: 'lof',
  male_count: 2,
  female_count: 3,
  puppies_available: null,
  price_cents: null,
  birth_date: '2026-10-27',
  expected_birth_date: null,
  available_from: '2026-12-22',
  photo_url: null,
  first_seen_at: '2026-10-28T09:00:00',
  last_seen_at: '2026-10-30T10:00:00',
  is_active: true,
  sources: ['centrale_canine'],
  follow_up_status: null,
  genetic_screening: null,
}

describe('LitterPresentation.buildBirthFact', (): void => {
  it('says when a litter was born, or when it is due', (): void => {
    expect(LitterPresentation.buildBirthFact(BORN_GOLD_LITTER)).toBe('Née le 27 oct.')
    expect(
      LitterPresentation.buildBirthFact({
        ...BORN_GOLD_LITTER,
        kind: 'litter_expected',
        birth_date: null,
        expected_birth_date: '2026-11-07',
      }),
    ).toBe('À naître vers le 7 nov.')
    expect(LitterPresentation.buildBirthFact({ ...BORN_GOLD_LITTER, birth_date: null })).toBeNull()
  })
})

describe('LitterPresentation price and sighting', (): void => {
  it('writes the price in euros, when a source gives one', (): void => {
    expect(LitterPresentation.buildPriceLabel(BORN_GOLD_LITTER)).toBeNull()
    expect(LitterPresentation.buildPriceLabel({ ...BORN_GOLD_LITTER, price_cents: 140_000 })).toBe('1\u202f400\u00a0€')
  })

  it('says since when a litter is gone from its sources', (): void => {
    expect(LitterPresentation.buildGoneSinceLabel(BORN_GOLD_LITTER)).toBeNull()
    expect(LitterPresentation.buildGoneSinceLabel({ ...BORN_GOLD_LITTER, is_active: false })).toBe(
      'Plus en ligne depuis le 30 oct.',
    )
  })
})

describe('LitterPresentation puppies available', (): void => {
  it('writes the puppies still offered, when a source tells', (): void => {
    expect(LitterPresentation.buildPuppiesAvailableLabel(BORN_GOLD_LITTER)).toBeNull()
    expect(LitterPresentation.buildPuppiesAvailableLabel({ ...BORN_GOLD_LITTER, puppies_available: 2 })).toBe(
      '2 chiots dispo',
    )
    expect(LitterPresentation.buildPuppiesAvailableLabel({ ...BORN_GOLD_LITTER, puppies_available: 1 })).toBe(
      '1 chiot dispo',
    )
    expect(LitterPresentation.buildPuppiesAvailableLabel({ ...BORN_GOLD_LITTER, puppies_available: 0 })).toBe(
      'Plus aucun chiot dispo',
    )
  })

  it('says nothing before the birth', (): void => {
    const expected: LitterCard = { ...BORN_GOLD_LITTER, kind: 'litter_expected', puppies_available: 0 }

    expect(LitterPresentation.buildPuppiesAvailableLabel(expected)).toBeNull()
    expect(LitterPresentation.arePuppiesAvailableWorthTelling(expected)).toBe(false)
  })

  it('is worth telling on a line only when it adds to the sexes', (): void => {
    expect(LitterPresentation.arePuppiesAvailableWorthTelling(BORN_GOLD_LITTER)).toBe(false)
    expect(LitterPresentation.arePuppiesAvailableWorthTelling({ ...BORN_GOLD_LITTER, puppies_available: 5 })).toBe(
      false,
    )
    expect(LitterPresentation.arePuppiesAvailableWorthTelling({ ...BORN_GOLD_LITTER, puppies_available: 1 })).toBe(true)
    expect(
      LitterPresentation.arePuppiesAvailableWorthTelling({
        ...BORN_GOLD_LITTER,
        male_count: null,
        female_count: null,
        puppies_available: 3,
      }),
    ).toBe(true)
  })
})
