import type { CentraleCanineRelayActivity, ListingSource, SourceActivity, SourceStatus } from '../app/types/api'
import type { AskedSourceRun, SourceRunCard, SourceRunContext, SourceRunEndNotice } from '../app/types/SourceRun'
import { describe, expect, it } from 'vitest'
import { SourceRunPresentation } from '../app/utils/sourceRunPresentation'

const SERVER_SOURCE: SourceStatus = {
  source: 'chiens_de_france',
  label: 'Chiens de France',
  is_collected: true,
  is_collected_by_desktop_app: false,
  last_run_at: '2026-11-01T09:20:00',
  last_status: 'ok',
  last_success_at: '2026-11-01T09:20:00',
  listings_seen: 12,
  error_message: null,
}

const RELAYED_SOURCE: SourceStatus = {
  ...SERVER_SOURCE,
  source: 'centrale_canine',
  label: 'Centrale Canine',
  is_collected_by_desktop_app: true,
}

const IDLE_RELAY: CentraleCanineRelayActivity = {
  is_relaying: false,
  source: null,
  pages_read_count: 0,
  pages_left_count: 0,
  is_requested: false,
  is_desktop_app_on: true,
}

/**
 * The activity the API answers.
 *
 * @param relay - What changes from a relay at rest, with a PC on.
 * @param runningSources - The sources the server reads.
 * @returns The activity.
 */
function activityWith(
  relay: Partial<CentraleCanineRelayActivity>,
  runningSources: ListingSource[] = [],
): SourceActivity {
  return { running_sources: runningSources, relay: { ...IDLE_RELAY, ...relay } }
}

const IPAD: SourceRunContext = {
  activity: activityWith({}),
  isDesktopApp: false,
  isRelayingHere: false,
  relayProgressHere: null,
}

const PC: SourceRunContext = { ...IPAD, isDesktopApp: true }

/**
 * The card of a source, nothing being sent from this device.
 *
 * @param status - The source status.
 * @param context - What runs now, and what this device is.
 * @returns The card.
 */
function cardOf(status: SourceStatus, context: SourceRunContext): SourceRunCard {
  return SourceRunPresentation.buildCard(status, context, false)
}

describe('SourceRunPresentation.buildCard', (): void => {
  it('loads the button of a source the server reads, wherever the run was asked', (): void => {
    const card: SourceRunCard = cardOf(SERVER_SOURCE, { ...IPAD, activity: activityWith({}, ['chiens_de_france']) })

    expect(card.phase).toBe('running_on_server')
    expect(card.button).toEqual({ label: 'Relevé en cours…', isLoading: true, isDisabled: true })
    expect(card.activityLine).toBeNull()
  })

  it('asks a PC from the iPad, then waits for it while a PC is on', (): void => {
    const idle: SourceRunCard = cardOf(RELAYED_SOURCE, IPAD)
    const waiting: SourceRunCard = cardOf(RELAYED_SOURCE, { ...IPAD, activity: activityWith({ is_requested: true }) })

    expect(idle.button).toEqual({ label: 'Demander un relevé', isLoading: false, isDisabled: false })
    expect(waiting.button).toEqual({ label: 'En attente du PC…', isLoading: true, isDisabled: true })
    expect(waiting.activityLine).toBe('Relevé demandé : un PC allumé le lance dans la minute.')
  })

  it('says the request waits for a PC to turn on when none is', (): void => {
    const card: SourceRunCard = cardOf(RELAYED_SOURCE, {
      ...IPAD,
      activity: activityWith({ is_requested: true, is_desktop_app_on: false }),
    })

    expect(card.phase).toBe('waiting_for_computer_to_turn_on')
    expect(card.button).toEqual({ label: 'Relevé demandé', isLoading: false, isDisabled: true })
    expect(card.activityLine).toBe(
      'Relevé demandé : aucun PC avec l’app n’est allumé, il partira dès qu’un PC l’ouvrira.',
    )
  })

  it('shows on the iPad how far the PC is', (): void => {
    const card: SourceRunCard = cardOf(RELAYED_SOURCE, {
      ...IPAD,
      activity: activityWith({ is_relaying: true, source: 'scc_breeders', pages_read_count: 12, pages_left_count: 8 }),
    })

    expect(card.button).toEqual({ label: 'Relevé en cours…', isLoading: true, isDisabled: true })
    expect(card.activityLine).toBe(
      'Relevé en cours depuis un PC : Annuaire des éleveurs (Centrale Canine), 12 pages lues, 8 à lire.',
    )
  })

  it('tells a PC whether the relay runs here or on another PC', (): void => {
    const here: SourceRunCard = cardOf(RELAYED_SOURCE, {
      ...PC,
      isRelayingHere: true,
      relayProgressHere: {
        source: 'centrale_canine',
        pagesReadCount: 1,
        pagesPlannedCount: 9,
        isWaitingForAnotherComputer: false,
      },
    })
    const elsewhere: SourceRunCard = cardOf(RELAYED_SOURCE, {
      ...PC,
      activity: activityWith({ is_relaying: true, source: 'scc_dogs', pages_read_count: 1, pages_left_count: 0 }),
    })
    const starting: SourceRunCard = cardOf(RELAYED_SOURCE, {
      ...IPAD,
      activity: activityWith({ is_relaying: true, source: 'centrale_canine', pages_left_count: 9 }),
    })
    const asked: SourceRunCard = cardOf(RELAYED_SOURCE, { ...PC, activity: activityWith({ is_requested: true }) })

    expect(here.activityLine).toBe('Relevé en cours depuis ce PC : Centrale Canine, 1 page lue sur 9.')
    expect(elsewhere.activityLine).toBe(
      'Relevé en cours depuis un autre PC : Fiches des chiens (Centrale Canine), 1 page lue.',
    )
    expect(starting.activityLine).toBe('Relevé en cours depuis un PC : Centrale Canine, 9 pages à lire.')
    expect(asked.button.label).toBe('Démarrage du relevé…')
    expect(cardOf(RELAYED_SOURCE, PC).button.label).toBe('Relever maintenant')
  })

  it('loads the button while this device sends its request', (): void => {
    expect(SourceRunPresentation.buildCard(SERVER_SOURCE, IPAD, true).button).toEqual({
      label: 'Relever maintenant',
      isLoading: true,
      isDisabled: true,
    })
  })
})

describe('SourceRunPresentation.hasRunEnded', (): void => {
  it('tells when a run of the server or a source of the relay ended', (): void => {
    const serverRunning: SourceActivity = activityWith({}, ['whoof'])
    const relayOnLitters: SourceActivity = activityWith({ is_relaying: true, source: 'centrale_canine' })
    const relayOnDirectory: SourceActivity = activityWith({ is_relaying: true, source: 'scc_breeders' })
    const relayAsked: SourceActivity = activityWith({ is_requested: true })
    const nothingRunning: SourceActivity = activityWith({})

    expect(SourceRunPresentation.hasRunEnded(null, serverRunning)).toBe(false)
    expect(SourceRunPresentation.hasRunEnded(nothingRunning, serverRunning)).toBe(false)
    expect(SourceRunPresentation.hasRunEnded(serverRunning, nothingRunning)).toBe(true)
    expect(SourceRunPresentation.hasRunEnded(relayOnLitters, relayOnLitters)).toBe(false)
    expect(SourceRunPresentation.hasRunEnded(relayOnLitters, relayOnDirectory)).toBe(true)
    expect(SourceRunPresentation.hasRunEnded(relayOnDirectory, nothingRunning)).toBe(true)
    expect(SourceRunPresentation.hasRunEnded(relayAsked, relayOnLitters)).toBe(false)
    expect(SourceRunPresentation.hasRunEnded(relayAsked, nothingRunning)).toBe(true)
  })
})

describe('SourceRunPresentation.buildRunEndNotice', (): void => {
  const directory: SourceStatus = {
    ...RELAYED_SOURCE,
    source: 'scc_breeders',
    label: 'L’annuaire de la Centrale Canine',
    last_run_at: '2026-10-31T07:10:00',
  }

  it('says done once the sources asked ran without failing', (): void => {
    const askedRun: AskedSourceRun = SourceRunPresentation.recordAskedRun(SERVER_SOURCE, [SERVER_SOURCE])

    const notice: SourceRunEndNotice = SourceRunPresentation.buildRunEndNotice(askedRun, [
      { ...SERVER_SOURCE, last_run_at: '2026-11-01T10:02:00' },
    ])

    expect(notice).toEqual({ title: 'Relevé terminé.', color: 'success' })
  })

  it('names the relayed sources that failed during the relay asked', (): void => {
    const askedRun: AskedSourceRun = SourceRunPresentation.recordAskedRun(RELAYED_SOURCE, [
      RELAYED_SOURCE,
      directory,
      SERVER_SOURCE,
    ])

    const notice: SourceRunEndNotice = SourceRunPresentation.buildRunEndNotice(askedRun, [
      { ...RELAYED_SOURCE, last_run_at: '2026-11-01T10:02:00' },
      { ...directory, last_run_at: '2026-11-01T10:03:00', last_status: 'error' },
      { ...SERVER_SOURCE, last_run_at: '2026-11-01T10:03:00', last_status: 'error' },
    ])

    expect(notice).toEqual({ title: 'Relevé en échec : L’annuaire de la Centrale Canine.', color: 'error' })
  })

  it('says the request was lost when nothing ran', (): void => {
    const askedRun: AskedSourceRun = SourceRunPresentation.recordAskedRun(RELAYED_SOURCE, [RELAYED_SOURCE])

    expect(SourceRunPresentation.buildRunEndNotice(askedRun, [RELAYED_SOURCE])).toEqual({
      title: 'Le relevé demandé n’a pas eu lieu : redemande-le.',
      color: 'neutral',
    })
  })
})
