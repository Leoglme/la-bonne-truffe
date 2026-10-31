import type { LitterCard } from '../app/types/api'
import type { DevicePosition } from '../app/types/Location'
import { describe, expect, it } from 'vitest'
import { LitterSorting } from '../app/utils/litterSorting'

const RENNES: DevicePosition = { latitude: 48.117, longitude: -1.678, recordedAt: '2026-10-30T10:00:00' }

/**
 * A card of the home with only the facts the sorts read.
 *
 * @param id - Its id, in the order of the API.
 * @param facts - Price, departure and position.
 * @returns The card.
 */
function buildCard(id: number, facts: Partial<LitterCard>): LitterCard {
  return {
    id,
    name: `Portée ${id}`,
    place: null,
    town: null,
    department_code: null,
    department_name: null,
    breeder_latitude: null,
    breeder_longitude: null,
    kind: 'litter_born',
    tier: 'preferred',
    score: 100 - id,
    colors: [],
    lof_status: 'lof',
    male_count: null,
    female_count: null,
    has_confirmed_sexes: false,
    puppies_available: null,
    price_cents: null,
    birth_date: null,
    expected_birth_date: null,
    available_from: null,
    photo_url: null,
    first_seen_at: '2026-10-28T09:00:00',
    last_seen_at: '2026-10-30T10:00:00',
    is_active: true,
    sources: ['centrale_canine'],
    follow_up_status: null,
    genetic_screening: null,
    ...facts,
  }
}

const CARDS: LitterCard[] = [
  buildCard(1, {
    price_cents: 140000,
    available_from: '2026-12-22',
    breeder_latitude: 47.65,
    breeder_longitude: -2.76,
  }),
  buildCard(2, { price_cents: null, available_from: '2026-11-30', breeder_latitude: 48.1, breeder_longitude: -1.7 }),
  buildCard(3, { price_cents: 120000, available_from: null, breeder_latitude: null, breeder_longitude: null }),
]

/**
 * The ids of sorted cards.
 *
 * @param cards - Sorted cards.
 * @returns Their ids.
 */
function idsOf(cards: LitterCard[]): number[] {
  return cards.map((card: LitterCard): number => card.id)
}

describe('LitterSorting.sort', (): void => {
  it('keeps the order of the API for the score', (): void => {
    expect(idsOf(LitterSorting.sort(CARDS, 'score', RENNES))).toEqual([1, 2, 3])
  })

  it('puts the closest first and the litters without a position last', (): void => {
    expect(idsOf(LitterSorting.sort(CARDS, 'distance', RENNES))).toEqual([2, 1, 3])
  })

  it('keeps the order of the API by distance while the device has no position', (): void => {
    expect(idsOf(LitterSorting.sort(CARDS, 'distance', null))).toEqual([1, 2, 3])
  })

  it('puts the cheapest first and the unknown prices last', (): void => {
    expect(idsOf(LitterSorting.sort(CARDS, 'price', RENNES))).toEqual([3, 1, 2])
  })

  it('orders the departures both ways, the unknown ones last', (): void => {
    expect(idsOf(LitterSorting.sort(CARDS, 'departure_soonest', RENNES))).toEqual([2, 1, 3])
    expect(idsOf(LitterSorting.sort(CARDS, 'departure_latest', RENNES))).toEqual([1, 2, 3])
  })
})
