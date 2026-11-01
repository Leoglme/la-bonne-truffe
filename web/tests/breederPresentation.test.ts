import type { BreederCard, BreederDetail, BreederDog, BreederLinkPreview, LitterCard } from '../app/types/api'
import type { BreederChip, BreederLinkRecognition, BreederSeenOnLink, BreederStat } from '../app/types/Breeder'
import type { LinkLogo } from '../app/types/UiLinkLogo'
import { describe, expect, it } from 'vitest'
import { BreederManualFormPresentation } from '../app/utils/breederManualFormPresentation'
import { BreederPresentation } from '../app/utils/breederPresentation'

const NOW: Date = new Date(2026, 10, 2, 9, 0)

const EXPECTED_GOLD_LITTER: LitterCard = {
  id: 1,
  name: 'Des Landes de Test',
  place: 'Ploërmel',
  town: 'Ploërmel',
  department_code: '56',
  department_name: 'Morbihan',
  breeder_latitude: null,
  breeder_longitude: null,
  kind: 'litter_expected',
  tier: 'preferred',
  score: 81,
  colors: [{ color: 'gold', confidence: 'inferred' }],
  lof_status: 'lof',
  male_count: null,
  female_count: null,
  puppies_available: null,
  price_cents: null,
  birth_date: null,
  expected_birth_date: '2026-11-07',
  available_from: null,
  photo_url: null,
  first_seen_at: '2026-09-05T09:00:00',
  last_seen_at: '2026-11-01T10:00:00',
  is_active: true,
  sources: ['centrale_canine'],
  follow_up_status: null,
  genetic_screening: null,
}

const BORN_GOLD_LITTER: LitterCard = {
  ...EXPECTED_GOLD_LITTER,
  id: 2,
  kind: 'litter_born',
  score: 96,
  colors: [{ color: 'gold', confidence: 'certain' }],
  male_count: 2,
  female_count: 3,
  puppies_available: 1,
  birth_date: '2026-09-14',
  expected_birth_date: null,
  available_from: '2026-11-09',
}

const BREEDER: BreederCard = {
  id: 7,
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
  is_selected_breeding: true,
  is_breed_club_member: true,
  has_siren: true,
  has_chiens_de_france_site: true,
  is_manual: false,
  sources: ['centrale_canine', 'chiens_de_france_sites'],
  gold_litters_count: 7,
  litters_count: 9,
  last_litter_date: '2026-09-14',
  litters_last_year_count: 4,
  breeding_females_count: 6,
  current_litter: EXPECTED_GOLD_LITTER,
  is_followed: true,
  follow_status: 'waiting',
}

const BREEDER_DETAIL: BreederDetail = {
  ...BREEDER,
  phone_e164: '+33612345678',
  siren: '812345678',
  website: null,
  chiens_de_france_site_url: 'https://landes-de-test.chiens-de-france.com',
  facebook_url: null,
  instagram_url: null,
  youtube_url: null,
  scc_breeder_id: '266172',
  links: [{ label: 'Facebook', url: 'https://www.facebook.com/landes-de-test' }],
  notes: null,
  chiens_de_france_registered_on: '2011-03-02',
  scc_last_litter_at: null,
  scc_directory_seen_at: null,
  litters: [EXPECTED_GOLD_LITTER, BORN_GOLD_LITTER],
  color_shares: [
    { color: 'gold', litters_count: 9 },
    { color: 'noir_et_feu', litters_count: 3 },
  ],
  reproducers: [],
  photos: [],
  follow: {
    status: 'waiting',
    notify_new_mating: true,
    notify_birth: true,
    notify_new_photos: true,
    notify_ignored_colors: false,
    next_reminder_at: '2026-11-08T08:00:00',
    last_contact_at: null,
    notes: [],
  },
}

const GOLD_STUD: BreederDog = {
  id: 11,
  role: 'reproducer',
  name: 'Père de test 11',
  full_name: 'Père de test 11 des Landes de Test',
  sex: 'male',
  birth_date: null,
  color: 'gold',
  color_code: 'F.Or.',
  rating: 1,
  health_codes: ['LocE-e/e', 'PRCD-1.1'],
  e_locus: 'e/e',
  carries_gold_by_parents: false,
  is_current_litter_parent: true,
  photos: ['https://landes-de-test.chiens-de-france.com/photo-de-test-1.jpg'],
  external_url: null,
  availability_text: null,
}

const CARRIER_LICE: BreederDog = {
  ...GOLD_STUD,
  id: 12,
  name: 'Mère de test 12',
  full_name: 'Mère de test 12 des Landes de Test',
  sex: 'female',
  color: 'bleu_rouan',
  color_code: 'Noi. Bla.Rou.',
  health_codes: [],
  e_locus: null,
  carries_gold_by_parents: true,
  photos: [],
}

const OTHER_DOGS: BreederDog[] = [21, 22, 23, 24].map((id: number): BreederDog => ({
  ...CARRIER_LICE,
  id,
  is_current_litter_parent: false,
  rating: null,
}))

describe('BreederPresentation.passesFilter', (): void => {
  it('keeps a breeder for the chips that describe it', (): void => {
    expect(BreederPresentation.passesFilter(BREEDER, 'all')).toBe(true)
    expect(BreederPresentation.passesFilter(BREEDER, 'followed')).toBe(true)
    expect(BreederPresentation.passesFilter(BREEDER, 'gold')).toBe(true)
    expect(BreederPresentation.passesFilter(BREEDER, 'club')).toBe(true)
    expect(BreederPresentation.passesFilter(BREEDER, 'active_litter')).toBe(true)
    expect(
      BreederPresentation.passesFilter(
        { ...BREEDER, is_followed: false, gold_litters_count: 0, is_breed_club_member: false, current_litter: null },
        'gold',
      ),
    ).toBe(false)
  })
})

describe('BreederPresentation.buildInitials', (): void => {
  it('takes the first letters of the significant words', (): void => {
    expect(BreederPresentation.buildInitials('Des Landes de Test')).toBe('LT')
    expect(BreederPresentation.buildInitials('Ar Mor Test')).toBe('AM')
    expect(BreederPresentation.buildInitials("Du Clos de l'Élevage A")).toBe('CÉ')
    expect(BreederPresentation.buildInitials('Kerlann')).toBe('K')
  })
})

describe('BreederPresentation.buildPlaceLine', (): void => {
  it('names the town and the department, then the distance when both positions are known', (): void => {
    expect(BreederPresentation.buildPlaceLine(BREEDER, null)).toBe('Ploërmel, Morbihan')
    expect(
      BreederPresentation.buildPlaceLine(BREEDER, { latitude: 48.11, longitude: -1.68, recordedAt: '2026-11-02' }),
    ).toBe('Ploërmel, Morbihan · à 57 km')
    expect(BreederPresentation.buildPlaceLine({ ...BREEDER, city: null, department_name: null }, null)).toBe(
      'Lieu à confirmer',
    )
  })
})

describe('BreederPresentation.buildLitterStatusLine', (): void => {
  it('tells about the current litter, hot when it calls for a call', (): void => {
    expect(BreederPresentation.buildLitterStatusLine(BREEDER, NOW)).toEqual({
      text: 'À naître vers le 7 nov. · gold',
      tone: 'hot',
    })
    expect(BreederPresentation.buildLitterStatusLine({ ...BREEDER, current_litter: BORN_GOLD_LITTER }, NOW)).toEqual({
      text: 'Née le 14 sept. · gold, 1 chiot dispo',
      tone: 'normal',
    })
    expect(
      BreederPresentation.buildLitterStatusLine(
        { ...BREEDER, current_litter: { ...BORN_GOLD_LITTER, puppies_available: null, birth_date: '2026-11-01' } },
        NOW,
      ),
    ).toEqual({ text: 'Née cette nuit · gold, 2 mâles et 3 femelles', tone: 'hot' })
  })

  it('falls back on the rhythm, the last litter, or says when nothing came for years', (): void => {
    expect(BreederPresentation.buildLitterStatusLine({ ...BREEDER, current_litter: null }, NOW)).toEqual({
      text: '4 portées l’an dernier · dernière en septembre',
      tone: 'normal',
    })
    expect(
      BreederPresentation.buildLitterStatusLine(
        { ...BREEDER, current_litter: null, litters_last_year_count: null, last_litter_date: '2026-06-03' },
        NOW,
      ),
    ).toEqual({ text: 'Dernière portée en juin 2026', tone: 'normal' })
    expect(
      BreederPresentation.buildLitterStatusLine(
        { ...BREEDER, current_litter: null, litters_last_year_count: null, last_litter_date: '2024-02-10' },
        NOW,
      ),
    ).toEqual({ text: 'Aucune portée depuis 2024', tone: 'inactive' })
    expect(
      BreederPresentation.buildLitterStatusLine(
        { ...BREEDER, current_litter: null, litters_last_year_count: null, last_litter_date: null },
        NOW,
      ),
    ).toEqual({ text: 'Aucune portée connue', tone: 'inactive' })
  })
})

describe('BreederPresentation.listChips', (): void => {
  it('vouches for what the sources say, in a stable order', (): void => {
    expect(BreederPresentation.listChips(BREEDER, true).map((chip: BreederChip): string => chip.label)).toEqual([
      'Sélectionné',
      'Spaniel Club',
      'Site Chiens de France',
      'Gold surtout',
    ])
    expect(BreederPresentation.listDetailChips(BREEDER_DETAIL).map((chip: BreederChip): string => chip.label)).toEqual([
      'Élevage sélectionné',
      'Membre du Spaniel Club Français',
      'SIREN vérifié',
      'Sur Chiens de France depuis 2011',
    ])
    expect(
      BreederPresentation.listChips({ ...BREEDER, gold_litters_count: 2, litters_count: 9 }, true).map(
        (chip: BreederChip): string => chip.label,
      ),
    ).not.toContain('Gold surtout')
  })
})

describe('BreederPresentation.buildStats', (): void => {
  it('counts the gold litters, dates the last one and gives the rhythm', (): void => {
    expect(BreederPresentation.buildStats(BREEDER_DETAIL).map((stat: BreederStat): string => stat.value)).toEqual([
      '7 sur 9',
      '14 sept.',
      '4 par an · 6 lices',
    ])
    expect(
      BreederPresentation.buildStats({
        ...BREEDER_DETAIL,
        gold_litters_count: 0,
        litters_count: 0,
        last_litter_date: null,
        litters_last_year_count: null,
        breeding_females_count: null,
      }).map((stat: BreederStat): string => stat.value),
    ).toEqual(['—', '—', '—'])
  })
})

describe('BreederPresentation.buildStats with the litters of its site', (): void => {
  it('gives the rhythm as the litters its site shows for the last year', (): void => {
    expect(
      BreederPresentation.buildStats({
        ...BREEDER_DETAIL,
        site_litters: [
          { birth_date: '2026-08-28', sire_name: 'Père de test 11', dam_name: 'Mère de test 12' },
          { birth_date: '2026-07-19', sire_name: null, dam_name: null },
          { birth_date: '2025-05-01', sire_name: null, dam_name: null },
        ],
      })[2]?.value,
    ).toBe('2 en 2026 · 6 lices')
  })
})

describe('BreederPresentation.buildColorShares', (): void => {
  it('turns the litters of each colour into percentages', (): void => {
    expect(BreederPresentation.buildColorShares(BREEDER_DETAIL)).toEqual([
      { label: 'Gold', percent: 75, swatch: '#E9B363', littersCount: 9 },
      { label: 'Noir et feu', percent: 25, swatch: '#3A2F2A', littersCount: 3 },
    ])
    expect(BreederPresentation.buildColorShares({ ...BREEDER_DETAIL, color_shares: [] })).toEqual([])
  })
})

describe('BreederPresentation.listSeenOnLinks', (): void => {
  it('lists the directories, then the site, then what was added by hand', (): void => {
    expect(BreederPresentation.listSeenOnLinks(BREEDER_DETAIL, NOW)).toEqual([
      {
        key: 'scc',
        logo: 'centrale_canine',
        label: 'Centrale Canine',
        description: 'Affixe déposé · SIREN 812 345 678',
        href: null,
      },
      {
        key: 'chiens-de-france',
        logo: 'chiens_de_france',
        label: 'Chiens de France',
        description: 'Site de l’élevage · ses chiens, ses futures portées',
        href: 'https://landes-de-test.chiens-de-france.com',
      },
      {
        key: 'link-0',
        logo: 'facebook',
        label: 'Facebook · ajouté par toi',
        description: 'facebook.com/landes-de-test',
        href: 'https://www.facebook.com/landes-de-test',
      },
    ])
  })

  it('lists the social accounts the Centrale Canine site declares, after the sites', (): void => {
    const links: BreederSeenOnLink[] = BreederPresentation.listSeenOnLinks(
      {
        ...BREEDER_DETAIL,
        links: [],
        facebook_url: 'https://www.facebook.com/landes.de.test',
        instagram_url: 'https://www.instagram.com/landes.de.test/',
        youtube_url: null,
      },
      NOW,
    )

    expect(links.map((link: BreederSeenOnLink): string => link.key)).toEqual([
      'scc',
      'chiens-de-france',
      'facebook',
      'instagram',
    ])
    expect(links[2]).toEqual({
      key: 'facebook',
      logo: 'facebook',
      label: 'Facebook',
      description: 'Page de l’élevage',
      href: 'https://www.facebook.com/landes.de.test',
    })
    expect(links[3]?.description).toBe('Compte de l’élevage')
  })
})

describe('BreederPresentation.listSeenOnLinks once the site is read', (): void => {
  it('says when the site was read and where each social link comes from', (): void => {
    const links: BreederSeenOnLink[] = BreederPresentation.listSeenOnLinks(
      {
        ...BREEDER_DETAIL,
        links: [],
        chiens_de_france_site_seen_at: '2026-11-02T06:40:00',
        facebook_url: 'https://www.facebook.com/landes.de.test',
        youtube_url: 'https://www.youtube.com/@landesdetest',
        social_link_origins: { facebook: 'breeder_site', youtube: 'added_by_hand' },
      },
      NOW,
    )

    expect(links.map((link: BreederSeenOnLink): string => link.description)).toEqual([
      'Affixe déposé · SIREN 812 345 678',
      'Site de l’élevage · relu ce matin',
      'Page de l’élevage · lien pris sur son site',
      'Chaîne de l’élevage · lien ajouté par toi',
    ])
  })
})

describe('BreederPresentation.listSeenOnLinks logos', (): void => {
  it('gives each link the logo of the site it leads to, and the globe to an unknown site', (): void => {
    const links: BreederSeenOnLink[] = BreederPresentation.listSeenOnLinks(
      {
        ...BREEDER_DETAIL,
        website: 'https://www.facebook.com/elevage.de.test',
        youtube_url: 'https://www.youtube.com/@landesdetest',
        links: [
          { label: 'Site', url: 'https://landes-de-test.chiens-de-france.com/cocker-spaniel-anglais' },
          { label: 'Instagram', url: 'https://instagram.com/landes.de.test' },
          { label: 'Leboncoin', url: 'https://www.leboncoin.fr/annonce-de-test' },
          { label: 'Site', url: 'pas une adresse' },
        ],
      },
      NOW,
    )

    expect(links.map((link: BreederSeenOnLink): LinkLogo => link.logo)).toEqual([
      'centrale_canine',
      'chiens_de_france',
      'facebook',
      'youtube',
      'chiens_de_france',
      'instagram',
      'website',
      'website',
    ])
  })
})

describe('BreederPresentation dogs', (): void => {
  it('words what a dog carries of the gold in place of its E locus code', (): void => {
    expect(BreederPresentation.buildDogFactsLine(GOLD_STUD)).toBe('Gold\u00a0· testé gold (e/e)\u00a0· PRCD-\u20601.1')
    expect(BreederPresentation.buildDogFactsLine(CARRIER_LICE)).toBe(
      'Bleu rouan\u00a0· porteuse du gold (E/e), d’après ses parents',
    )
  })

  it('never cuts a health code at its hyphens, nor starts a line with a dot', (): void => {
    const factsLine: string | null = BreederPresentation.buildDogFactsLine({
      ...GOLD_STUD,
      health_codes: ['PL-1-l/l', 'LocB-B/b'],
    })

    expect(factsLine).toBe('Gold\u00a0· testé gold (e/e)\u00a0· PL-\u20601-\u2060l/l\u00a0· LocB-\u2060B/b')
  })

  it('names the rating agreed with the sex', (): void => {
    expect(BreederPresentation.buildDogRatingLabel(GOLD_STUD)).toBe('Confirmé')
    expect(BreederPresentation.buildDogRatingLabel(CARRIER_LICE)).toBe('Confirmée')
    expect(BreederPresentation.buildDogRatingLabel({ ...GOLD_STUD, rating: null })).toBeNull()
  })

  it('shows the parents of its current litters, then the next dogs up to four', (): void => {
    const reproducers: BreederDog[] = [GOLD_STUD, CARRIER_LICE, ...OTHER_DOGS]

    expect(
      BreederPresentation.listShownDogs({ ...BREEDER_DETAIL, reproducers }).map((dog: BreederDog): number => dog.id),
    ).toEqual([11, 12, 21, 22])
    expect(
      BreederPresentation.listShownDogs({
        ...BREEDER_DETAIL,
        reproducers: reproducers.map((dog: BreederDog): BreederDog => ({ ...dog, is_current_litter_parent: true })),
      }),
    ).toHaveLength(6)
    expect(BreederPresentation.buildHiddenDogsLabel(34, true)).toBe('34 autres chiens sur son site')
    expect(BreederPresentation.buildHiddenDogsLabel(1, false)).toBe('1 autre chien')
  })
})

describe('BreederPresentation.buildSiteLittersLink', (): void => {
  it('opens the litters its site shows for the last year', (): void => {
    const siteLittersUrl: string = 'https://landes-de-test.chiens-de-france.com/cocker-spaniel-anglais/chiots-vendus'

    expect(
      BreederPresentation.buildSiteLittersLink({
        ...BREEDER_DETAIL,
        site_litters_url: siteLittersUrl,
        site_litters: [
          { birth_date: '2026-08-28', sire_name: null, dam_name: null },
          { birth_date: '2026-07-19', sire_name: null, dam_name: null },
        ],
      }),
    ).toEqual({ label: 'Ses 2 portées de 2026, en photos sur son site', href: siteLittersUrl })
    expect(
      BreederPresentation.buildSiteLittersLink({
        ...BREEDER_DETAIL,
        site_litters_url: siteLittersUrl,
        site_litters: [{ birth_date: '2025-04-02', sire_name: null, dam_name: null }],
      })?.label,
    ).toBe('Sa portée de 2025, en photos sur son site')
    expect(BreederPresentation.buildSiteLittersLink(BREEDER_DETAIL)).toBeNull()
  })
})

describe('BreederPresentation.buildLinkRecognition', (): void => {
  const facebookPreview: BreederLinkPreview = {
    kind: 'facebook',
    address: 'https://www.facebook.com/landes.de.test',
    social_accounts: [],
    is_page_read: false,
  }
  const websitePreview: BreederLinkPreview = {
    kind: 'website',
    address: 'https://www.landes-de-test.fr',
    social_accounts: [
      { account: 'facebook', url: 'https://www.facebook.com/landes.de.test' },
      { account: 'instagram', url: 'https://www.instagram.com/landes.de.test/' },
      { account: 'youtube', url: 'https://www.youtube.com/@landesdetest' },
    ],
    is_page_read: true,
  }

  it('says that the site of Chiens de France will be read', (): void => {
    expect(
      BreederPresentation.buildLinkRecognition(
        { ...facebookPreview, kind: 'chiens_de_france_site', address: 'https://landes-de-test.chiens-de-france.com' },
        BREEDER_DETAIL,
      ).title,
    ).toBe('Son site Chiens de France')
  })

  it('tells whether a social account comes, is known or replaces the one known', (): void => {
    expect(BreederPresentation.buildLinkRecognition(facebookPreview, BREEDER_DETAIL)).toEqual({
      title: 'Sa page Facebook',
      helper: 'Elle ira dans « Vu sur ».',
      accountLabels: [],
    })
    expect(
      BreederPresentation.buildLinkRecognition(facebookPreview, {
        ...BREEDER_DETAIL,
        facebook_url: 'https://www.facebook.com/landes.de.test',
      }).helper,
    ).toBe('Elle est déjà dans « Vu sur ».')
    expect(
      BreederPresentation.buildLinkRecognition(facebookPreview, {
        ...BREEDER_DETAIL,
        facebook_url: 'https://www.facebook.com/ancienne.page',
      }).helper,
    ).toBe('Elle remplacera celle de « Vu sur ».')
  })

  it('lists the accounts at the bottom of another site, and which ones « Vu sur » lacks', (): void => {
    expect(BreederPresentation.buildLinkRecognition(websitePreview, BREEDER_DETAIL)).toEqual<BreederLinkRecognition>({
      title: 'Le site de l’élevage',
      helper: 'En bas de sa page, trois comptes. Ils iront dans « Vu sur ».',
      accountLabels: ['Facebook', 'Instagram', 'YouTube'],
    })
    expect(
      BreederPresentation.buildLinkRecognition(websitePreview, {
        ...BREEDER_DETAIL,
        facebook_url: 'https://www.facebook.com/landes.de.test',
      }).helper,
    ).toBe('En bas de sa page, trois comptes. Ceux qui manquent iront dans « Vu sur ».')
    expect(
      BreederPresentation.buildLinkRecognition({ ...websitePreview, is_page_read: false }, BREEDER_DETAIL).title,
    ).toBe('Une autre page')
  })
})

describe('BreederPresentation.resolvePrimaryAction', (): void => {
  it('calls when the phone is known, else opens the site', (): void => {
    expect(BreederPresentation.resolvePrimaryAction(BREEDER_DETAIL)).toEqual({
      href: 'tel:+33612345678',
      label: 'Appeler l’éleveur',
      isCall: true,
    })
    expect(BreederPresentation.resolvePrimaryAction({ ...BREEDER_DETAIL, phone_e164: null })).toEqual({
      href: 'https://landes-de-test.chiens-de-france.com',
      label: 'Voir le site de l’élevage',
      isCall: false,
    })
    expect(
      BreederPresentation.resolvePrimaryAction({
        ...BREEDER_DETAIL,
        phone_e164: null,
        chiens_de_france_site_url: null,
      }),
    ).toBeNull()
  })
})

describe('BreederPresentation.buildReminderLabel', (): void => {
  it('words the reminder of a follow', (): void => {
    expect(BreederPresentation.buildReminderLabel(BREEDER_DETAIL.follow!)).toMatch(/^Rappel · /)
    expect(BreederPresentation.buildReminderLabel({ ...BREEDER_DETAIL.follow!, next_reminder_at: null })).toBeNull()
  })
})

describe('BreederManualFormPresentation.buildPayload', (): void => {
  it('tells the town from the postal code and labels the link by its site', (): void => {
    expect(
      BreederManualFormPresentation.buildPayload(
        {
          display_name: ' Élevage des Joyaux du Lac ',
          place: 'Guer, 56380',
          link: 'facebook.com/elevagedesjoyauxdulac',
          phone: '06 12 34 56 78',
          note: 'Vu sur Facebook',
        },
        true,
      ),
    ).toEqual({
      display_name: 'Élevage des Joyaux du Lac',
      city: 'Guer',
      zip_code: '56380',
      phone: '06 12 34 56 78',
      links: [{ label: 'Facebook', url: 'https://facebook.com/elevagedesjoyauxdulac' }],
      notes: 'Vu sur Facebook',
      follow: true,
    })
    expect(
      BreederManualFormPresentation.buildPayload(
        { display_name: 'Kerlann', place: '', link: '', phone: '', note: '' },
        false,
      ),
    ).toEqual({
      display_name: 'Kerlann',
      city: null,
      zip_code: null,
      phone: null,
      links: [],
      notes: null,
      follow: false,
    })
    expect(
      BreederManualFormPresentation.buildPayload(
        { display_name: '  ', place: '', link: '', phone: '', note: '' },
        true,
      ),
    ).toBeNull()
  })
})
