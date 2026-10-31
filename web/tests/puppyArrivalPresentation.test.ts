import type { LitterDetail } from '../app/types/api'
import { describe, expect, it } from 'vitest'
import { PuppyArrivalPresentation } from '../app/utils/puppyArrivalPresentation'

const NOW: Date = new Date(2026, 9, 31, 10, 0)

const RESERVED_LITTER: LitterDetail = {
  id: 5,
  name: 'Des Bords de Vilaine',
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
  follow_up_status: 'reserved',
  genetic_screening: null,
  reasons: [],
  flags: [],
  litter_number: null,
  mating_date: null,
  sire: null,
  dam: null,
  breeder: {
    display_name: 'Marie Le Gall',
    affix: 'Des Bords de Vilaine',
    city: 'Redon',
    phone_e164: null,
    siren: null,
    website: null,
    is_selected_breeding: false,
    has_affix: true,
    is_breed_club_member: false,
  },
  photos: [],
  listings: [],
  follow_up: null,
}

describe('PuppyArrivalPresentation', (): void => {
  it('counts down to the arrival day', (): void => {
    const daysLeft: number = PuppyArrivalPresentation.countDaysLeft('2026-11-23', NOW)

    expect(daysLeft).toBe(23)
    expect(PuppyArrivalPresentation.buildCountdownBadge(daysLeft)).toBe('J-23')
    expect(PuppyArrivalPresentation.buildTitle(daysLeft)).toBe('Plus que 23 jours')
    expect(PuppyArrivalPresentation.buildArrivalDayLabel('2026-11-23', daysLeft)).toBe('Il arrive le 23 novembre')
  })

  it('greets the last day, the day itself and the days after', (): void => {
    expect(PuppyArrivalPresentation.buildTitle(1)).toBe('Plus qu’un jour')
    expect(PuppyArrivalPresentation.buildTitle(0)).toBe('C’est le grand jour')
    expect(PuppyArrivalPresentation.buildCountdownBadge(0)).toBeNull()
    expect(PuppyArrivalPresentation.buildArrivalDayLabel('2026-10-31', 0)).toBe('Il arrive aujourd’hui')
    expect(PuppyArrivalPresentation.buildTitle(-2)).toBe('Bienvenue à la maison')
    expect(PuppyArrivalPresentation.buildArrivalDayLabel('2026-10-29', -2)).toBe('Il est arrivé le 29 octobre')
  })

  it('says whose puppy it is', (): void => {
    expect(PuppyArrivalPresentation.buildSentence(RESERVED_LITTER)).toBe(
      'Ton chiot gold Des Bords de Vilaine, chez Marie Le Gall à Redon.',
    )
    expect(PuppyArrivalPresentation.buildSentence(null)).toBe('Ton chiot arrive bientôt.')
  })

  it('counts only the preparations of the list', (): void => {
    expect(PuppyArrivalPresentation.countDonePreparations(['basket', 'old_key', 'bowls'])).toBe(2)
  })

  it('offers the departure day of the litter, or today once it is past', (): void => {
    expect(PuppyArrivalPresentation.suggestArrivalDay(RESERVED_LITTER, NOW)).toBe('2026-12-22')
    expect(PuppyArrivalPresentation.suggestArrivalDay({ ...RESERVED_LITTER, available_from: '2026-10-01' }, NOW)).toBe(
      '2026-10-31',
    )
  })
})
