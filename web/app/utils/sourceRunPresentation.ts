import type { CentraleCanineRelayActivity, ListingSource, SourceActivity, SourceStatus } from '~/types/api'
import type { CentraleCanineRelayProgress } from '~/types/CentraleCanineRelay'
import type {
  AskedSourceRun,
  SourceRunButton,
  SourceRunCard,
  SourceRunContext,
  SourceRunEndNotice,
  SourceRunPhase,
} from '~/types/SourceRun'
import { LISTING_SOURCE_LABELS } from '~/constants/litterLabels'
import { FrenchText } from '~/utils/frenchText'

/** How a source card reads while its relevé runs: on the server, on this PC, on another PC, or waiting for a PC. */
export class SourceRunPresentation {
  /**
   * Build what a source card shows: where its relevé stands, its button, and the line under it.
   *
   * @param status - The source status.
   * @param context - What runs now, and what this device is.
   * @param isAskedHere - Whether this device is sending the request of this source right now.
   * @returns The card.
   */
  static buildCard(status: SourceStatus, context: SourceRunContext, isAskedHere: boolean): SourceRunCard {
    const phase: SourceRunPhase = this.resolvePhase(status, context)
    return {
      status,
      phase,
      button: this.buildButton(status, phase, context.isDesktopApp, isAskedHere),
      activityLine: this.buildActivityLine(phase, context),
    }
  }

  /**
   * Tell where the relevé of a source stands: a source the server reads runs or not; a source the desktop app
   * relays is read by this PC, by another one, or waits for a PC.
   *
   * @param status - The source status.
   * @param context - What runs now, and what this device is.
   * @returns The phase.
   */
  static resolvePhase(status: SourceStatus, context: SourceRunContext): SourceRunPhase {
    if (!status.is_collected_by_desktop_app) {
      return context.activity?.running_sources.includes(status.source) ? 'running_on_server' : 'idle'
    }
    if (context.isRelayingHere) {
      return 'relaying_here'
    }
    const relay: CentraleCanineRelayActivity | null = context.activity?.relay ?? null
    if (relay?.is_relaying) {
      return 'relaying_elsewhere'
    }
    if (relay?.is_requested) {
      return relay.is_desktop_app_on ? 'waiting_for_computer' : 'waiting_for_computer_to_turn_on'
    }
    return 'idle'
  }

  /**
   * Whether the relevé of a source is under way, or asked and waiting for a PC.
   *
   * @param phase - Where the relevé stands.
   * @returns False only when nothing runs nor waits.
   */
  static isUnderWay(phase: SourceRunPhase): boolean {
    return phase !== 'idle'
  }

  /**
   * Build the run button: it loads on every device while the relevé runs, or while a PC that is on is about to
   * take it.
   *
   * @param status - The source status.
   * @param phase - Where its relevé stands.
   * @param isDesktopApp - Whether this device is a PC with the app, which relays the Centrale Canine itself.
   * @param isAskedHere - Whether this device is sending the request right now.
   * @returns The label, and whether the button loads or is disabled.
   */
  static buildButton(
    status: SourceStatus,
    phase: SourceRunPhase,
    isDesktopApp: boolean,
    isAskedHere: boolean,
  ): SourceRunButton {
    if (phase === 'waiting_for_computer_to_turn_on') {
      return { label: 'Relevé demandé', isLoading: false, isDisabled: true }
    }
    if (phase === 'waiting_for_computer') {
      return { label: isDesktopApp ? 'Démarrage du relevé…' : 'En attente du PC…', isLoading: true, isDisabled: true }
    }
    if (phase !== 'idle') {
      return { label: 'Relevé en cours…', isLoading: true, isDisabled: true }
    }
    const label: string =
      status.is_collected_by_desktop_app && !isDesktopApp ? 'Demander un relevé' : 'Relever maintenant'
    return { label, isLoading: isAskedHere, isDisabled: isAskedHere }
  }

  /**
   * Build the line under a relayed source while its relevé runs or waits for a PC.
   *
   * @param phase - Where the relevé stands.
   * @param context - What runs now, and what this device is.
   * @returns The line, or null when there is nothing to say.
   */
  static buildActivityLine(phase: SourceRunPhase, context: SourceRunContext): string | null {
    if (phase === 'relaying_here') {
      return this.buildRelayHereLine(context.relayProgressHere)
    }
    if (phase === 'relaying_elsewhere') {
      return this.buildRelayElsewhereLine(context.activity?.relay ?? null, context.isDesktopApp)
    }
    if (phase === 'waiting_for_computer') {
      return context.isDesktopApp
        ? 'Relevé demandé : il démarre dans un instant.'
        : 'Relevé demandé : un PC allumé le lance dans la minute.'
    }
    if (phase === 'waiting_for_computer_to_turn_on') {
      return 'Relevé demandé : aucun PC avec l’app n’est allumé, il partira dès qu’un PC l’ouvrira.'
    }
    return null
  }

  /**
   * Build the line of the relay this PC runs: the source and the pages read in this round, or the wait for
   * another PC.
   *
   * @param progress - Where the relay of this PC stands.
   * @returns « Relevé en cours depuis ce PC : Centrale Canine, 3 pages lues sur 9. »
   */
  static buildRelayHereLine(progress: CentraleCanineRelayProgress | null): string {
    if (progress?.isWaitingForAnotherComputer) {
      return 'Un autre PC relève la Centrale Canine : ton relevé partira dès qu’il aura fini…'
    }
    if (progress === null || progress.source === null) {
      return 'Relevé en cours depuis ce PC…'
    }
    const pagesRead: string = `${progress.pagesReadCount} ${FrenchText.pickForm(progress.pagesReadCount, 'page lue', 'pages lues')}`
    return `Relevé en cours depuis ce PC : ${LISTING_SOURCE_LABELS[progress.source]}, ${pagesRead} sur ${progress.pagesPlannedCount}.`
  }

  /**
   * Build the line of the relay another PC runs, as it last told the API.
   *
   * @param relay - Where the relay stands.
   * @param isDesktopApp - Whether this device is itself a PC with the app.
   * @returns « Relevé en cours depuis un PC : Centrale Canine, 12 pages lues, 8 à lire. »
   */
  static buildRelayElsewhereLine(relay: CentraleCanineRelayActivity | null, isDesktopApp: boolean): string {
    const computer: string = isDesktopApp ? 'un autre PC' : 'un PC'
    if (relay === null || relay.source === null) {
      return `Relevé en cours depuis ${computer}…`
    }
    const pages: string | null = this.buildRelayPagesPart(relay.pages_read_count, relay.pages_left_count)
    const source: string = LISTING_SOURCE_LABELS[relay.source]
    return pages === null
      ? `Relevé en cours depuis ${computer} : ${source}.`
      : `Relevé en cours depuis ${computer} : ${source}, ${pages}.`
  }

  /**
   * Say how far the relay of another PC is in its source.
   *
   * @param pagesReadCount - Pages of the source read so far.
   * @param pagesLeftCount - Pages of the source still to read.
   * @returns « 12 pages lues, 8 à lire », « 9 pages à lire », « 12 pages lues », or null before any page is asked.
   */
  static buildRelayPagesPart(pagesReadCount: number, pagesLeftCount: number): string | null {
    const pagesRead: string = `${pagesReadCount} ${FrenchText.pickForm(pagesReadCount, 'page lue', 'pages lues')}`
    if (pagesReadCount > 0 && pagesLeftCount > 0) {
      return `${pagesRead}, ${pagesLeftCount} à lire`
    }
    if (pagesReadCount > 0) {
      return pagesRead
    }
    if (pagesLeftCount > 0) {
      return `${pagesLeftCount} ${FrenchText.pickForm(pagesLeftCount, 'page', 'pages')} à lire`
    }
    return null
  }

  /**
   * Note the time of the last run of every source as this device asks a relevé, to tell afterwards which sources
   * the relevé ran.
   *
   * @param status - The source asked.
   * @param statuses - Every source status, as shown now.
   * @returns The relevé asked.
   */
  static recordAskedRun(status: SourceStatus, statuses: SourceStatus[]): AskedSourceRun {
    return {
      source: status.source,
      isRelayed: status.is_collected_by_desktop_app,
      lastRunTimesBefore: Object.fromEntries(
        statuses.map((sourceStatus: SourceStatus): [string, string | null] => [
          sourceStatus.source,
          sourceStatus.last_run_at,
        ]),
      ),
    }
  }

  /**
   * Build the notice of a relevé this device asked, once it is over: the sources it ran (the asked one, or every
   * relayed one for a relay), and those that failed.
   *
   * @param askedRun - The relevé asked from this device.
   * @param statuses - Every source status, reloaded after the relevé.
   * @returns « Relevé terminé. », « Relevé en échec : … », or the request lost before any run.
   */
  static buildRunEndNotice(askedRun: AskedSourceRun, statuses: SourceStatus[]): SourceRunEndNotice {
    const ranStatuses: SourceStatus[] = statuses.filter(
      (status: SourceStatus): boolean =>
        (askedRun.isRelayed ? status.is_collected_by_desktop_app : status.source === askedRun.source) &&
        status.last_run_at !== (askedRun.lastRunTimesBefore[status.source] ?? null),
    )
    if (ranStatuses.length === 0) {
      return { title: 'Le relevé demandé n’a pas eu lieu : redemande-le.', color: 'neutral' }
    }
    const failedLabels: string[] = ranStatuses
      .filter((status: SourceStatus): boolean => status.last_status === 'error')
      .map((status: SourceStatus): string => status.label)
    if (failedLabels.length > 0) {
      return { title: `Relevé en échec : ${failedLabels.join(', ')}.`, color: 'error' }
    }
    return { title: 'Relevé terminé.', color: 'success' }
  }

  /**
   * Whether a relevé ended between two readings of the activity, whose statuses are then worth reloading: a run of
   * the server, a source of the relay, or a relay asked that is no longer waiting nor running (done while this
   * device was not looking, or lost).
   *
   * @param previous - The activity read before, null on the first reading.
   * @param next - The activity just read.
   * @returns True when a source stopped running.
   */
  static hasRunEnded(previous: SourceActivity | null, next: SourceActivity): boolean {
    if (previous === null) {
      return false
    }
    const hasServerRunEnded: boolean = previous.running_sources.some(
      (source: ListingSource): boolean => !next.running_sources.includes(source),
    )
    if (hasServerRunEnded) {
      return true
    }
    const previousRelay: CentraleCanineRelayActivity | null = previous.relay
    const nextRelay: CentraleCanineRelayActivity | null = next.relay
    if (previousRelay?.is_relaying) {
      return nextRelay === null || !nextRelay.is_relaying || nextRelay.source !== previousRelay.source
    }
    if (previousRelay?.is_requested) {
      return nextRelay === null || (!nextRelay.is_requested && !nextRelay.is_relaying)
    }
    return false
  }
}
