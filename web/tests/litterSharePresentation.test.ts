import type { LitterCard } from '../app/types/api'
import { describe, expect, it } from 'vitest'
import { LitterSharePresentation } from '../app/utils/litterSharePresentation'

const BORN_GOLD_LITTER: LitterCard = {
  id: 1,
  name: 'Des Bords de Vilaine',
  place: 'Redon',
  town: 'Redon',
  department_code: '35',
  department_name: 'Ille-et-Vilaine',
  breeder_latitude: null,
  breeder_longitude: null,
  kind: 'litter_born',
  tier: null,
  score: null,
  colors: [{ color: 'gold', confidence: 'certain' }],
  lof_status: 'lof',
  male_count: 2,
  female_count: 3,
  has_confirmed_sexes: false,
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

describe('LitterSharePresentation', (): void => {
  it('sums up a born litter in one line', (): void => {
    expect(LitterSharePresentation.buildSummaryLine(BORN_GOLD_LITTER)).toBe(
      'Née le 27 oct. · gold · 2 mâles, 3 femelles',
    )
    expect(LitterSharePresentation.buildBirthLabel(BORN_GOLD_LITTER)).toBe('NÉE LE 27 OCT.')
  })

  it('sums up a litter to come without colour nor sexes', (): void => {
    const expectedLitter: LitterCard = {
      ...BORN_GOLD_LITTER,
      kind: 'litter_expected',
      colors: [],
      male_count: null,
      female_count: null,
      birth_date: null,
      expected_birth_date: '2026-07-07',
    }

    expect(LitterSharePresentation.buildSummaryLine(expectedLitter)).toBe('À naître vers le 7 juil.')
  })

  it('names who shared the litter', (): void => {
    expect(LitterSharePresentation.buildTitle('Léo')).toBe('Léo t’a partagé une portée')
    expect(LitterSharePresentation.buildTitle('  ')).toBe('On t’a partagé une portée')
  })
})
