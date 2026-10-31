import type { LitterCard } from '../app/types/api'
import type { LitterMapCluster, LitterMapPlace, ScreenPoint } from '../app/types/LitterMap'
import type { GeographicPoint } from '../app/types/Location'
import { describe, expect, it } from 'vitest'
import { LitterMapPlaces } from '../app/utils/litterMapPlaces'

/**
 * A card of the home with only the facts the map reads.
 *
 * @param id - Its id.
 * @param facts - Name, score and position.
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
    score: null,
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

/**
 * The ids of the litters of each place or cluster.
 *
 * @param groups - Places or clusters.
 * @returns Their litter ids.
 */
function litterIdsOf(groups: (LitterMapPlace | LitterMapCluster)[]): number[][] {
  return groups.map((group: LitterMapPlace | LitterMapCluster): number[] =>
    group.litters.map((litter: LitterCard): number => litter.id),
  )
}

/**
 * A flat projection: 100 pixels per degree.
 *
 * @param point - A geographic point.
 * @returns Its position on screen.
 */
function projectAt100PixelsPerDegree(point: GeographicPoint): ScreenPoint {
  return { x: point.longitude * 100, y: -point.latitude * 100 }
}

const REDON: Partial<LitterCard> = { breeder_latitude: 47.65, breeder_longitude: -2.08 }

describe('LitterMapPlaces.groupByPosition', (): void => {
  it('gives one place to the litters of the same address and none to a litter without a position', (): void => {
    const places: LitterMapPlace[] = LitterMapPlaces.groupByPosition([
      buildCard(1, { ...REDON, score: 88 }),
      buildCard(2, { breeder_latitude: 48.1, breeder_longitude: -1.7, score: 96 }),
      buildCard(3, { ...REDON, score: 70 }),
      buildCard(4, {}),
    ])

    expect(litterIdsOf(places)).toEqual([[1, 3], [2]])
    expect(places[0]?.point).toEqual({ latitude: 47.65, longitude: -2.08 })
  })
})

describe('LitterMapPlaces.cluster', (): void => {
  it('gathers the places whose pins would overlap, around the first one', (): void => {
    const places: LitterMapPlace[] = LitterMapPlaces.groupByPosition([
      buildCard(1, { breeder_latitude: 48, breeder_longitude: -1.7 }),
      buildCard(2, { breeder_latitude: 48.1, breeder_longitude: -1 }),
      buildCard(3, { breeder_latitude: 48, breeder_longitude: 0 }),
    ])

    const clusters: LitterMapCluster[] = LitterMapPlaces.cluster(places, projectAt100PixelsPerDegree)

    expect(litterIdsOf(clusters)).toEqual([[1, 2], [3]])
    expect(clusters[0]?.point).toEqual({ latitude: 48, longitude: -1.7 })
  })
})

describe('LitterMapPlaces.pointsToOpenOn', (): void => {
  const places: LitterMapPlace[] = LitterMapPlaces.groupByPosition([
    buildCard(1, { breeder_latitude: 48.39, breeder_longitude: -4.49 }),
    buildCard(2, { breeder_latitude: 48.12, breeder_longitude: -1.6 }),
    buildCard(3, { breeder_latitude: 47.22, breeder_longitude: -1.55 }),
  ])

  it('opens on the home and its closest places', (): void => {
    const home: GeographicPoint = { latitude: 48.11, longitude: -1.68 }

    expect(LitterMapPlaces.pointsToOpenOn(places, home, 2)).toEqual([
      home,
      { latitude: 48.12, longitude: -1.6 },
      { latitude: 47.22, longitude: -1.55 },
    ])
  })

  it('opens on every place while the home is unknown', (): void => {
    expect(LitterMapPlaces.pointsToOpenOn(places, null, 2)).toHaveLength(3)
  })
})

describe('LitterMapPlaces.buildPinLabel', (): void => {
  it('names a lone litter with its score, and counts several', (): void => {
    expect(LitterMapPlaces.buildPinLabel([buildCard(1, { name: 'De Kerlann', score: 88 })])).toBe('De Kerlann, 88 %')
    expect(LitterMapPlaces.buildPinLabel([buildCard(1, { name: 'De Kerlann' })])).toBe('De Kerlann, –')
    expect(LitterMapPlaces.buildPinLabel([buildCard(1, {}), buildCard(2, {})])).toBe('2 portées')
  })
})
