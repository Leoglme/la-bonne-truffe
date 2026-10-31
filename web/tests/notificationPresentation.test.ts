import type { NotificationLitter, SentNotification } from '../app/types/api'
import type { NotificationDaySection } from '../app/types/Notification'
import { describe, expect, it } from 'vitest'
import { FrenchDate } from '../app/utils/frenchDate'
import { NotificationPresentation } from '../app/utils/notificationPresentation'

const NOW: Date = FrenchDate.parseApiDate('2026-10-30T19:00:00')

const BORN_LITTER: NotificationLitter = {
  id: 1,
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
  puppies_available: 1,
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
  breeder_phone_e164: '+33679846555',
  digest_event: null,
}

/**
 * Build a sent « née » notification about the gold litter.
 *
 * @param id - Its id.
 * @param sentAt - Sending time, from the API.
 * @returns The notification.
 */
function buildBornNotification(id: number, sentAt: string): SentNotification {
  return {
    id,
    kind: 'born',
    title: 'Portée née · Des Bords de Vilaine',
    body: 'b',
    url: '/portees/1',
    litter_group_id: 1,
    sent_at: sentAt,
    read_at: null,
    litter: BORN_LITTER,
    litters: [],
  }
}

describe('NotificationPresentation', (): void => {
  it('groups the notifications by day, dropping the empty days', (): void => {
    const sections: NotificationDaySection[] = NotificationPresentation.groupByDay(
      [
        buildBornNotification(3, '2026-10-30T18:40:00'),
        buildBornNotification(2, '2026-10-29T08:00:00'),
        buildBornNotification(1, '2026-10-20T08:00:00'),
      ],
      NOW,
    )

    expect(
      sections.map((section: NotificationDaySection): [string, number[]] => [
        section.title,
        section.notifications.map((notification: SentNotification): number => notification.id),
      ]),
    ).toEqual([
      ['Aujourd’hui', [3]],
      ['Hier', [2]],
      ['Plus tôt', [1]],
    ])
  })

  it('writes the time as short as the day allows', (): void => {
    expect(NotificationPresentation.buildTimeLabel('2026-10-30T18:40:00', NOW)).toBe('il y a 20 min')
    expect(NotificationPresentation.buildTimeLabel('2026-10-30T17:50:00', NOW)).toBe('il y a 1 h')
    expect(NotificationPresentation.buildTimeLabel('2026-10-29T08:00:00', NOW)).toBe('hier')
    expect(NotificationPresentation.buildTimeLabel('2026-10-20T08:00:00', NOW)).toBe('20 oct.')
  })

  it('writes the facts of a litter around its sexes', (): void => {
    expect(NotificationPresentation.buildAvailabilityFact(BORN_LITTER)).toBe('dispo vers le 22 déc.')
    expect(NotificationPresentation.buildPlaceAndColorLine(BORN_LITTER, null)).toBe('Redon · gold')
  })

  it('writes the puppies a followed litter still offers', (): void => {
    expect(NotificationPresentation.buildPuppiesLeftPhrase(BORN_LITTER)).toBe('plus qu’un chiot disponible')
    expect(NotificationPresentation.buildPuppiesLeftPhrase({ ...BORN_LITTER, puppies_available: 3 })).toBe(
      'plus que 3 chiots disponibles',
    )
    expect(NotificationPresentation.buildPuppiesLeftPhrase({ ...BORN_LITTER, puppies_available: 0 })).toBe(
      'plus aucun chiot disponible',
    )
  })
})
