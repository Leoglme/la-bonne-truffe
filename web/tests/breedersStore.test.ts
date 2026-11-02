import type { Mock } from 'vitest'
import type { BreederCard, BreederDetail } from '../app/types/api'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { BreedersService } from '../app/services/breedersService'
import { useBreedersStore } from '../app/stores/breeders'

vi.mock('../app/services/breedersService', (): { BreedersService: { addLink: Mock } } => ({
  BreedersService: { addLink: vi.fn() },
}))

const BREEDER_ID: number = 7
const SITE_URL: string = 'https://landes-de-test.chiens-de-france.com'

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
  phone_e164: null,
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

describe('useBreedersStore().addLink', (): void => {
  beforeEach((): void => {
    setActivePinia(createPinia())
    vi.mocked(BreedersService.addLink).mockResolvedValue({
      ...BREEDER_DETAIL,
      has_chiens_de_france_site: true,
      chiens_de_france_site_url: SITE_URL,
      website: SITE_URL,
    })
  })

  afterEach((): void => {
    vi.clearAllMocks()
  })

  it('sends the link as pasted, then shows the breeder with it in the list and on its page', async (): Promise<void> => {
    const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
    breedersStore.cards = [BREEDER_CARD]
    breedersStore.selectedBreeder = BREEDER_DETAIL

    await breedersStore.addLink(BREEDER_ID, 'landes-de-test.chiens-de-france.com/cocker-spaniel-anglais/chiots')

    expect(BreedersService.addLink).toHaveBeenCalledWith(BREEDER_ID, {
      url: 'landes-de-test.chiens-de-france.com/cocker-spaniel-anglais/chiots',
    })
    expect(breedersStore.selectedBreeder?.chiens_de_france_site_url).toBe(SITE_URL)
    expect(breedersStore.cards[0]?.has_chiens_de_france_site).toBe(true)
  })
})

describe('useBreedersStore() choices', (): void => {
  const keptChoices: Map<string, string> = new Map()

  beforeEach((): void => {
    setActivePinia(createPinia())
    keptChoices.clear()
    vi.stubGlobal('localStorage', {
      getItem: (key: string): string | null => keptChoices.get(key) ?? null,
      setItem: (key: string, value: string): void => {
        keptChoices.set(key, value)
      },
    })
  })

  afterEach((): void => {
    vi.unstubAllGlobals()
  })

  it('opens on the filter and sort chosen at the last visit', (): void => {
    useBreedersStore().selectFilter('followed')
    useBreedersStore().selectSort('name')
    setActivePinia(createPinia())

    const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
    breedersStore.restoreSavedChoices()

    expect([breedersStore.selectedFilterKey, breedersStore.selectedSortKey]).toEqual(['followed', 'name'])
  })
})
