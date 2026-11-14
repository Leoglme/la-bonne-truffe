import type { CoatColor, LitterDetail, LitterSourceListing } from '../app/types/api'
import type { LitterPuppyLine } from '../app/types/Litter'
import { describe, expect, it } from 'vitest'
import { LitterDetailPresentation } from '../app/utils/litterDetailPresentation'

const NOW: Date = new Date(2026, 10, 1, 9, 0)

const BIRTH_DECLARATION: LitterSourceListing = {
  id: 11,
  source: 'centrale_canine',
  kind: 'litter_born',
  external_url: 'https://www.centrale-canine.fr/portee/test',
  litter_number: '2026024873',
  last_seen_at: '2026-11-01T06:40:00',
  is_active: true,
  male_count: 1,
  female_count: 2,
  colors: [],
  photos: [],
  puppy_state: null,
  price_cents: null,
}

const LITTER_PAGE_URL: string = 'https://elevage-a.chiens-de-france.com/cocker-spaniel-anglais/chiots-a-vendre/495610'

const MALE_PUPPY_AD: LitterSourceListing = {
  id: 12,
  source: 'chiens_de_france',
  kind: 'puppy_ad',
  external_url: `${LITTER_PAGE_URL}#:~:text=2199888`,
  litter_number: null,
  last_seen_at: '2026-11-01T06:40:00',
  is_active: true,
  male_count: 1,
  female_count: 0,
  colors: [{ color: 'gold', confidence: 'certain' }],
  photos: ['https://elevage-a.chiens-de-france.com/photo-de-test-1.jpg'],
  puppy_state: 'available',
  price_cents: 140000,
}

const FEMALE_PUPPY_AD: LitterSourceListing = {
  ...MALE_PUPPY_AD,
  id: 13,
  external_url: `${LITTER_PAGE_URL}#:~:text=2199889`,
  male_count: 0,
  female_count: 1,
  colors: [{ color: 'bleu_rouan', confidence: 'certain' }],
  photos: ['https://elevage-a.chiens-de-france.com/photo-de-test-2.jpg'],
  puppy_state: 'reserved',
  price_cents: null,
}

const SOLD_PUPPY_AD: LitterSourceListing = {
  ...FEMALE_PUPPY_AD,
  id: 14,
  photos: [],
  puppy_state: 'sold',
  last_seen_at: '2026-10-31T06:40:00',
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
  puppies_available: 1,
  price_cents: 140000,
  birth_date: '2026-10-20',
  expected_birth_date: null,
  available_from: '2026-12-15',
  photo_url: null,
  first_seen_at: '2026-10-21T09:00:00',
  latest_listing_appeared_at: '2026-10-21T09:00:00',
  last_seen_at: '2026-11-01T06:40:00',
  is_active: true,
  sources: ['centrale_canine', 'chiens_de_france'],
  follow_up_status: null,
  genetic_screening: null,
  reasons: [],
  flags: [],
  litter_number: '2026024873',
  mating_date: null,
  sire: null,
  dam: null,
  breeder: null,
  photos: [],
  listings: [BIRTH_DECLARATION, MALE_PUPPY_AD, FEMALE_PUPPY_AD, SOLD_PUPPY_AD],
  follow_up: null,
  photos_added_at: null,
}

describe('LitterDetailPresentation.buildBreederPhoneLabel', (): void => {
  it('writes a French number by pairs, any other unchanged', (): void => {
    expect(LitterDetailPresentation.buildBreederPhoneLabel('+33679846555')).toBe('06 79 84 65 55')
    expect(LitterDetailPresentation.buildBreederPhoneLabel('+32475123456')).toBe('+32475123456')
  })
})

describe('LitterDetailPresentation.buildParentRatingLabel', (): void => {
  it('names the level of a father', (): void => {
    expect(LitterDetailPresentation.buildParentRatingLabel(1, 'sire')).toBe('Confirmé')
    expect(LitterDetailPresentation.buildParentRatingLabel(6, 'sire')).toBe('Élite A')
  })

  it('agrees the level with a mother', (): void => {
    expect(LitterDetailPresentation.buildParentRatingLabel(4, 'dam')).toBe('Recommandée')
  })

  it('keeps the number of a level outside the grid', (): void => {
    expect(LitterDetailPresentation.buildParentRatingLabel(7, 'dam')).toBe('Niveau 7 sur 6')
  })
})

describe('LitterDetailPresentation.buildPhotoBadge', (): void => {
  it('tells new photos the day they came and the next one', (): void => {
    expect(LitterDetailPresentation.buildPhotoBadge({ ...LITTER, photos_added_at: '2026-11-01T06:40:00' }, NOW)).toBe(
      'NOUVELLES PHOTOS · CE MATIN',
    )
    expect(LitterDetailPresentation.buildPhotoBadge({ ...LITTER, photos_added_at: '2026-10-31T14:00:00' }, NOW)).toBe(
      'NOUVELLES PHOTOS · HIER',
    )
    expect(
      LitterDetailPresentation.buildPhotoBadge({ ...LITTER, photos_added_at: '2026-10-29T06:40:00' }, NOW),
    ).toBeNull()
  })

  it('keeps a litter to come or born last night first', (): void => {
    expect(
      LitterDetailPresentation.buildPhotoBadge(
        { ...LITTER, kind: 'litter_expected', photos_added_at: '2026-11-01T06:40:00' },
        NOW,
      ),
    ).toBe('À NAÎTRE')
  })
})

describe('LitterDetailPresentation.buildListingLines', (): void => {
  it('gathers the puppy ads of a source in one line of « Vu sur », linked to the page of the litter', (): void => {
    expect(LitterDetailPresentation.buildListingLines(LITTER)).toMatchObject([
      {
        description: 'Centrale Canine · déclaration de naissance',
        href: 'https://www.centrale-canine.fr/portee/test',
      },
      {
        description: 'Chiens de France · 2 chiots en photo',
        href: LITTER_PAGE_URL,
      },
    ])
  })

  it('links the puppy ads of a site that gives each puppy its own page to the first one', (): void => {
    const puppyPageUrl: string = 'https://www.chiens-de-france.com/chiot/2199888'

    expect(
      LitterDetailPresentation.buildListingLines({
        ...LITTER,
        listings: [{ ...MALE_PUPPY_AD, external_url: puppyPageUrl }],
      }),
    ).toMatchObject([{ href: puppyPageUrl }])
  })
})

describe('LitterDetailPresentation.buildPuppyLines', (): void => {
  it('names each puppy, its sex and where it stands', (): void => {
    expect(LitterDetailPresentation.buildPuppyLines(LITTER)).toMatchObject([
      { label: 'Chiot 1', sexLabel: 'mâle', color: 'gold', stateLabel: 'Disponible · 1\u202f400\u00a0€' },
      { label: 'Chiot 2', sexLabel: 'femelle', color: 'bleu_rouan', stateLabel: 'Réservée' },
      { label: 'Chiot 3', sexLabel: 'femelle', color: 'bleu_rouan', stateLabel: 'Vendue' },
    ])
  })

  it('says when an ad that told nothing is gone', (): void => {
    expect(
      LitterDetailPresentation.buildPuppyLines({
        ...LITTER,
        listings: [{ ...MALE_PUPPY_AD, puppy_state: null, is_active: false }],
      })[0],
    ).toMatchObject({ label: 'Chiot', stateLabel: 'Plus en ligne', isGone: true })
  })

  it('links each puppy to its place on the page of its litter', (): void => {
    expect(LitterDetailPresentation.buildPuppyLines(LITTER)[0]?.href).toBe(`${LITTER_PAGE_URL}#:~:text=2199888`)
  })

  it('draws in gold a puppy whose ad tells no colour when both parents only give the gold', (): void => {
    const listings: LitterSourceListing[] = [{ ...MALE_PUPPY_AD, colors: [] }, FEMALE_PUPPY_AD]
    const readColors: (goldPuppyOdds: number) => (CoatColor | null)[] = (goldPuppyOdds: number): (CoatColor | null)[] =>
      LitterDetailPresentation.buildPuppyLines({ ...LITTER, listings, gold_puppy_odds: goldPuppyOdds }).map(
        (line: LitterPuppyLine): CoatColor | null => line.color,
      )

    expect(readColors(1)).toEqual(['gold', 'bleu_rouan'])
    expect(readColors(0.5)).toEqual([null, 'bleu_rouan'])
  })

  it('tells the colour noted by hand first, then the one the ad gives for sure, and nothing for a bundle', (): void => {
    const listings: LitterSourceListing[] = [
      { ...MALE_PUPPY_AD, confirmed_color: 'noir_et_feu' },
      { ...FEMALE_PUPPY_AD, colors: [{ color: 'gold', confidence: 'ambiguous' }] },
      SOLD_PUPPY_AD,
    ]

    expect(
      LitterDetailPresentation.buildPuppyLines({ ...LITTER, listings }).map(
        (line: LitterPuppyLine): [number, CoatColor | null] => [line.listingId, line.knownColor],
      ),
    ).toEqual([
      [12, 'noir_et_feu'],
      [13, null],
      [14, 'bleu_rouan'],
    ])
  })
})

describe('LitterDetailPresentation.buildPuppiesCaption', (): void => {
  it('says where and when the puppy ads were seen last', (): void => {
    expect(LitterDetailPresentation.buildPuppiesCaption(LITTER.listings, NOW)).toBe('Sur Chiens de France, ce matin')
    expect(
      LitterDetailPresentation.buildPuppiesCaption(
        [SOLD_PUPPY_AD, { ...SOLD_PUPPY_AD, source: 'chiots_de_france' }],
        NOW,
      ),
    ).toBe('Vus hier')
    expect(LitterDetailPresentation.buildPuppiesCaption([BIRTH_DECLARATION], NOW)).toBeNull()
  })
})

describe('LitterDetailPresentation.resolvePrimaryAction', (): void => {
  it('opens the page of the litter when the breeder has no phone and a puppy ad comes first', (): void => {
    expect(
      LitterDetailPresentation.resolvePrimaryAction({ ...LITTER, listings: [MALE_PUPPY_AD, BIRTH_DECLARATION] }),
    ).toEqual({ href: LITTER_PAGE_URL, label: 'Voir sur Chiens de France', isCall: false })
  })
})
