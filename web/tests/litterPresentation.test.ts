import type { LitterCard } from '../app/types/api'
import type { DevicePosition } from '../app/types/Location'
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
  latest_listing_appeared_at: '2026-10-28T09:00:00',
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

  it('writes the lowest and the highest price when the puppies do not all ask the same', (): void => {
    const litterFrom1600Euros: LitterCard = { ...BORN_GOLD_LITTER, price_cents: 160_000 }

    expect(LitterPresentation.buildPriceLabel({ ...litterFrom1600Euros, highest_price_cents: 165_000 })).toBe(
      '1\u202f600\u00a0à\u00a01\u202f650\u00a0€',
    )
    expect(LitterPresentation.buildPriceLabel({ ...litterFrom1600Euros, highest_price_cents: 160_000 })).toBe(
      '1\u202f600\u00a0€',
    )
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

describe('LitterPresentation driving time', (): void => {
  const HOME: DevicePosition = { latitude: 48.117, longitude: -1.678, recordedAt: '2026-10-31T10:00:00Z' }
  const NEARBY_LITTER: LitterCard = {
    ...BORN_GOLD_LITTER,
    place: 'Bain-de-Bretagne',
    breeder_latitude: 47.841,
    breeder_longitude: -1.674,
  }

  it('writes the drive in minutes, then in hours, never split across lines', (): void => {
    expect(LitterPresentation.buildDrivingTimeLabel(37)).toBe('37\u00a0min')
    expect(LitterPresentation.buildDrivingTimeLabel(60)).toBe('1\u00a0h')
    expect(LitterPresentation.buildDrivingTimeLabel(65)).toBe('1\u00a0h\u00a005')
  })

  it('adds the drive after the distance, only when the distance is known', (): void => {
    expect(LitterPresentation.buildPlaceLine(NEARBY_LITTER, HOME, 37)).toBe('Bain-de-Bretagne · à 31 km · 37\u00a0min')
    expect(LitterPresentation.buildPlaceLine(NEARBY_LITTER, HOME)).toBe('Bain-de-Bretagne · à 31 km')
    expect(LitterPresentation.buildPlaceLine(NEARBY_LITTER, null, 37)).toBe('Bain-de-Bretagne')
  })
})

describe('LitterPresentation.matchesSearchQuery', (): void => {
  const BRITTANY_LITTER: LitterCard = {
    ...BORN_GOLD_LITTER,
    name: 'Des Vents d’Océan',
    place: 'La Grée-Saint-Laurent',
    town: 'La Grée-Saint-Laurent',
    department_code: '56',
    department_name: 'Morbihan',
  }

  it('keeps a litter whose breeding, town or department hold every word typed, accents and capitals aside', (): void => {
    expect(LitterPresentation.matchesSearchQuery(BRITTANY_LITTER, 'vents ocean')).toBe(true)
    expect(LitterPresentation.matchesSearchQuery(BRITTANY_LITTER, 'OCÉAN')).toBe(true)
    expect(LitterPresentation.matchesSearchQuery(BRITTANY_LITTER, 'gree saint laurent')).toBe(true)
    expect(LitterPresentation.matchesSearchQuery(BRITTANY_LITTER, 'morbihan')).toBe(true)
    expect(LitterPresentation.matchesSearchQuery(BRITTANY_LITTER, '56')).toBe(true)
  })

  it('leaves out a litter missing one word, and keeps every litter while nothing is typed', (): void => {
    expect(LitterPresentation.matchesSearchQuery(BRITTANY_LITTER, 'vents redon')).toBe(false)
    expect(LitterPresentation.matchesSearchQuery(BORN_GOLD_LITTER, '')).toBe(true)
    expect(LitterPresentation.matchesSearchQuery(BORN_GOLD_LITTER, '   ')).toBe(true)
  })
})

describe('LitterPresentation.resolveIllustrationCoat', (): void => {
  it('draws the coat of a single certain colour, and the « autre » coat when that colour has no drawing', (): void => {
    expect(LitterPresentation.resolveIllustrationCoat([{ color: 'gold', confidence: 'certain' }])).toBe('gold')
    expect(LitterPresentation.resolveIllustrationCoat([{ color: 'marron_et_feu', confidence: 'certain' }])).toBe(
      'autre',
    )
  })

  it('draws the question mark coat while the colour is not known for sure', (): void => {
    expect(LitterPresentation.resolveIllustrationCoat([])).toBe('inconnue')
    expect(LitterPresentation.resolveIllustrationCoat([{ color: 'noir', confidence: 'ambiguous' }])).toBe('inconnue')
    expect(LitterPresentation.resolveIllustrationCoat([{ color: 'inconnue', confidence: 'certain' }])).toBe('inconnue')
    expect(
      LitterPresentation.resolveIllustrationCoat([
        { color: 'gold', confidence: 'certain' },
        { color: 'noir', confidence: 'certain' },
      ]),
    ).toBe('inconnue')
  })
})
