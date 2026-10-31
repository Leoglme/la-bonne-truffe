<template>
  <UiTabScreen title="Sources" subtitle="Où la truffe cherche, toutes les heures.">
    <div class="flex flex-col gap-3.5">
      <p v-if="sourcesStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ sourcesStore.loadError }}
      </p>
      <UiSectionCard v-for="status in sourcesStore.statuses" :key="status.source" class="gap-3">
        <span class="flex items-center gap-2.5">
          <span
            class="size-[9px] shrink-0 rounded-full"
            :class="status.last_status ? SOURCE_RUN_STATUS_DOT_CLASSES[status.last_status] : 'bg-line-strong'"
            aria-hidden="true"
          />
          <h2 class="m-0 font-display text-[22px] font-semibold">{{ status.label }}</h2>
        </span>
        <p class="m-0 text-[15px] text-ink-muted">{{ buildSourceStatusLine(status) }}</p>
        <p v-if="status.is_collected_by_desktop_app" class="m-0 text-sm text-ink-muted">
          Relevée par l’app Windows, quand un PC où elle tourne est allumé.
        </p>
        <p v-if="status.last_status === 'error' && status.error_message" class="m-0 text-sm text-coral-text">
          {{ status.error_message }}
        </p>
        <p
          v-if="status.is_collected_by_desktop_app && centraleCanineRelayStore.isRelaying"
          class="m-0 text-sm font-bold text-ink-secondary"
          aria-live="polite"
        >
          {{ relayProgressLine }}
        </p>
        <p
          v-if="status.is_collected_by_desktop_app && centraleCanineRelayStore.lastRelayErrorMessage"
          class="m-0 text-sm text-coral-text"
        >
          Relais depuis ce PC en échec : {{ centraleCanineRelayStore.lastRelayErrorMessage }}
        </p>
        <p
          v-if="runErrorSource === status.source && runError"
          role="alert"
          class="m-0 text-sm font-bold text-coral-text"
        >
          {{ runError }}
        </p>
        <UButton
          v-if="status.is_collected"
          size="xl"
          class="mt-1 w-full justify-center md:w-auto md:self-start"
          :loading="runningSource === status.source"
          :disabled="runningSource !== null || isRelayRunningHereFor(status)"
          @click="runNow(status)"
        >
          {{ buildRunButtonLabel(status) }}
        </UButton>
      </UiSectionCard>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { CentraleCanineRelayAnswer, ListingSource, SourceRunStatus, SourceStatus } from '~/types/api'
import type { CentraleCanineRelayProgress } from '~/types/CentraleCanineRelay'
import { computed, onMounted, ref } from 'vue'
import { LISTING_SOURCE_LABELS } from '~/constants/litterLabels'
import { SourcesService } from '~/services/sourcesService'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'

useHead({ title: 'Sources · La Bonne Truffe' })

const sourcesStore: ReturnType<typeof useSourcesStore> = useSourcesStore()
const centraleCanineRelayStore: ReturnType<typeof useCentraleCanineRelayStore> = useCentraleCanineRelayStore()
const { isDesktopApp }: ReturnType<typeof useDesktopRuntime> = useDesktopRuntime()
const toast: ReturnType<typeof useToast> = useToast()

const SOURCE_RUN_STATUS_DOT_CLASSES: Record<SourceRunStatus, string> = {
  ok: 'bg-online',
  error: 'bg-coral-text',
  running: 'bg-line-strong',
}

const runningSource: Ref<ListingSource | null> = ref(null)
const runError: Ref<string | null> = ref(null)
const runErrorSource: Ref<ListingSource | null> = ref(null)

const relayProgressLine: ComputedRef<string> = computed((): string => {
  const progress: CentraleCanineRelayProgress | null = centraleCanineRelayStore.relayProgress
  if (progress?.isWaitingForAnotherComputer) {
    return 'Un autre PC relève la Centrale Canine : ton relevé partira dès qu’il aura fini…'
  }
  if (progress === null || progress.source === null) {
    return 'Relevé en cours depuis ce PC…'
  }
  const pages: string = `${progress.pagesReadCount} ${FrenchText.pickForm(progress.pagesReadCount, 'page lue', 'pages lues')} sur ${progress.pagesPlannedCount}`
  return `Relevé en cours depuis ce PC : ${LISTING_SOURCE_LABELS[progress.source]}, ${pages}.`
})

/**
 * Build the line under a source.
 *
 * @param status - The source status.
 * @returns « Relevé il y a 12 min · 19 portées vues », or why there is none.
 */
function buildSourceStatusLine(status: SourceStatus): string {
  if (!status.is_collected) {
    return 'Pas encore relevée.'
  }
  if (status.last_run_at === null) {
    return 'Aucun relevé pour l’instant.'
  }
  const timeSinceRun: string = FrenchDate.formatTimeSince(FrenchDate.parseApiDate(status.last_run_at), new Date())

  if (status.last_status === 'error' && status.last_success_at !== null) {
    const timeSinceSuccess: string = FrenchDate.formatTimeSince(
      FrenchDate.parseApiDate(status.last_success_at),
      new Date(),
    )
    return `Dernier relevé en échec, ${timeSinceRun} · dernier réussi ${timeSinceSuccess}.`
  }
  if (status.last_status === 'error') {
    return `Dernier relevé en échec, ${timeSinceRun}.`
  }
  const seenCount: number = status.listings_seen ?? 0
  return `Relevé ${timeSinceRun} · ${seenCount} ${FrenchText.pickForm(seenCount, 'portée vue', 'portées vues')}`
}

/**
 * Whether the relay of this computer is reading the sources the desktop app relays, which includes this one.
 *
 * @param status - The source status.
 * @returns True while a relay runs here and the source is one of those it reads.
 */
function isRelayRunningHereFor(status: SourceStatus): boolean {
  return status.is_collected_by_desktop_app && isDesktopApp.value && centraleCanineRelayStore.isRelaying
}

/**
 * Build the label of the run button: a source the desktop app reads can only be asked for away from a computer.
 *
 * @param status - The source status.
 * @returns « Relever maintenant », « Demander un relevé », or the label of the run in progress.
 */
function buildRunButtonLabel(status: SourceStatus): string {
  if (runningSource.value === status.source || isRelayRunningHereFor(status)) {
    return 'Relevé en cours…'
  }
  if (status.is_collected_by_desktop_app && !isDesktopApp.value) {
    return 'Demander un relevé'
  }
  return 'Relever maintenant'
}

/**
 * Run a collection now and refresh the statuses: on the server, on this computer, or by asking a computer that is on.
 *
 * @param status - The source status.
 */
async function runNow(status: SourceStatus): Promise<void> {
  runningSource.value = status.source
  runError.value = null
  runErrorSource.value = status.source
  try {
    if (!status.is_collected_by_desktop_app) {
      sourcesStore.statuses = await SourcesService.run(status.source)
    } else if (isDesktopApp.value) {
      await relayCentraleCanineNow()
    } else {
      await askAComputerToRelayCentraleCanine()
    }
  } catch (error: unknown) {
    runError.value = error instanceof Error ? error.message : 'Relevé impossible'
  } finally {
    runningSource.value = null
  }
}

/**
 * Relay the Centrale Canine from this computer now, every source in a row; the relay store refreshes the
 * statuses after the last run.
 */
async function relayCentraleCanineNow(): Promise<void> {
  if (centraleCanineRelayStore.isRelaying) {
    runError.value = 'Un relevé est déjà en cours depuis ce PC : il relève les trois sources à la suite.'
    return
  }
  const answer: CentraleCanineRelayAnswer | null = await centraleCanineRelayStore.relay(true)
  if (answer === null) {
    runError.value = 'Relevé impossible pour l’instant : reconnecte-toi, puis réessaie.'
    return
  }
  if (answer.state === 'busy') {
    runError.value =
      'Un autre PC relève la Centrale Canine depuis plus de dix minutes : ton relevé partira dès qu’il aura fini.'
    return
  }
  if (answer.state === 'not_due') {
    toast.add({ title: 'Rien à relever pour l’instant.', color: 'neutral' })
    return
  }
  if (answer.state === 'run_finished') {
    toast.add({ title: 'Relevé terminé.', color: 'success' })
    return
  }
  runError.value = 'Le relevé s’est arrêté avant la fin : il reprendra à la prochaine vérification.'
}

/**
 * Ask the desktop app of a computer that is on to relay the Centrale Canine at its next check.
 */
async function askAComputerToRelayCentraleCanine(): Promise<void> {
  await SourcesService.requestCentraleCanineRelay()
  toast.add({
    title:
      'Relevé demandé : un PC allumé avec l’app relèvera les portées, l’annuaire et les fiches dans les 5 minutes.',
    color: 'success',
  })
}

onMounted((): Promise<void> => sourcesStore.load())
</script>
