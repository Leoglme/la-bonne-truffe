import type { Mock } from 'vitest'
import type { BreederCard, BreederDetail, LitterDetail } from '../app/types/api'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { BreedersService } from '../app/services/breedersService'
import { LittersService } from '../app/services/littersService'
import { useBreedersStore } from '../app/stores/breeders'
import { useLittersStore } from '../app/stores/litters'

vi.mock('../app/services/littersService', (): { LittersService: { setFollowUp: Mock } } => ({
  LittersService: { setFollowUp: vi.fn() },
}))
vi.mock('../app/services/breedersService', (): { BreedersService: { get: Mock } } => ({
  BreedersService: { get: vi.fn() },
}))

const BREEDER_ID: number = 7

const LITTER: LitterDetail = {
  id: 1,
  name: 'Des Landes de Test',
  place: 'Ploërmel',
  town: 'Ploërmel',
  department_code: '56',
  department_name: 'Morbihan',
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
  birth_date: '2026-10-29',
  expected_birth_date: null,
  available_from: '2026-12-24',
  photo_url: null,
  first_seen_at: '2026-10-30T09:00:00',
  latest_listing_appeared_at: '2026-10-30T09:00:00',
  last_seen_at: '2026-11-01T10:00:00',
  is_active: true,
  sources: ['centrale_canine'],
  follow_up_status: null,
  genetic_screening: null,
  reasons: [],
  flags: [],
  litter_number: null,
  mating_date: null,
  sire: null,
  dam: null,
  breeder: {
    id: BREEDER_ID,
    display_name: 'Marie de Test',
    affix: 'Des Landes de Test',
    city: 'Ploërmel',
    phone_e164: '+33612345678',
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

const FOLLOWED_LITTER: LitterDetail = {
  ...LITTER,
  follow_up_status: 'to_contact',
  follow_up: { status: 'to_contact', next_reminder_at: null, last_contact_at: null, notes: [] },
}

const BREEDER_CARD: BreederCard = {
  id: BREEDER_ID,
  name: 'Des Landes de Test',
  person_name: 'Marie de Test',
  affix: 'Des Landes de Test',
  city: 'Ploërmel',
  zip_code: '56800',
  department_code: '56',
  department_name: 'Morbihan',
  latitude: 47.93,
  longitude: -2.4,
  logo_url: null,
  photo_url: null,
  is_selected_breeding: false,
  is_breed_club_member: false,
  has_siren: false,
  has_chiens_de_france_site: false,
  is_manual: false,
  sources: ['centrale_canine'],
  gold_litters_count: 1,
  litters_count: 1,
  last_litter_date: '2026-10-29',
  litters_last_year_count: 1,
  breeding_females_count: null,
  current_litter: null,
  is_followed: false,
  follow_status: null,
}

const BREEDER_DETAIL: BreederDetail = {
  ...BREEDER_CARD,
  phone_e164: '+33612345678',
  siren: null,
  website: null,
  chiens_de_france_site_url: null,
  facebook_url: null,
  instagram_url: null,
  youtube_url: null,
  scc_breeder_id: '266172',
  links: [],
  notes: null,
  chiens_de_france_registered_on: null,
  scc_last_litter_at: null,
  scc_directory_seen_at: null,
  litters: [],
  color_shares: [],
  reproducers: [],
  photos: [],
  follow: null,
}

const FOLLOWED_BREEDER_DETAIL: BreederDetail = {
  ...BREEDER_DETAIL,
  is_followed: true,
  follow_status: 'to_contact',
  follow: {
    status: 'to_contact',
    notify_new_mating: true,
    notify_birth: true,
    notify_new_photos: true,
    notify_ignored_colors: false,
    next_reminder_at: null,
    last_contact_at: null,
    notes: [],
  },
}

describe('useLittersStore().follow', (): void => {
  beforeEach((): void => {
    setActivePinia(createPinia())
    vi.stubGlobal('useLocationStore', (): { position: null } => ({ position: null }))
    vi.stubGlobal('useBreedersStore', useBreedersStore)
    vi.mocked(LittersService.setFollowUp).mockResolvedValue(FOLLOWED_LITTER)
    vi.mocked(BreedersService.get).mockResolvedValue(FOLLOWED_BREEDER_DETAIL)
  })

  afterEach((): void => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('shows the breeder of the litter as followed in the Éleveurs tab, without reloading it', async (): Promise<void> => {
    const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
    breedersStore.cards = [BREEDER_CARD]
    breedersStore.selectedBreeder = BREEDER_DETAIL
    breedersStore.selectFilter('followed')

    const detail: LitterDetail = await useLittersStore().follow(LITTER)

    expect(detail.follow_up?.status).toBe('to_contact')
    expect(BreedersService.get).toHaveBeenCalledWith(BREEDER_ID)
    await vi.waitFor((): void => {
      expect(breedersStore.filteredCards.map((card: BreederCard): number => card.id)).toEqual([BREEDER_ID])
    })
    expect(breedersStore.selectedBreeder?.follow?.status).toBe('to_contact')
  })

  it('reads no breeder when the litter has none known', async (): Promise<void> => {
    vi.mocked(LittersService.setFollowUp).mockResolvedValue({ ...FOLLOWED_LITTER, breeder: null })

    await useLittersStore().follow({ ...LITTER, breeder: null })

    expect(BreedersService.get).not.toHaveBeenCalled()
  })

  it('keeps the litter followed when its breeder cannot be read again', async (): Promise<void> => {
    vi.mocked(BreedersService.get).mockRejectedValue(new Error('Réseau indisponible'))
    const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
    littersStore.selectedLitter = LITTER

    await littersStore.follow(LITTER)

    expect(littersStore.selectedLitter?.follow_up?.status).toBe('to_contact')
  })
})
