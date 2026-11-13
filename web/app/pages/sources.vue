<template>
  <UiTabScreen title="Sources" subtitle="Où la truffe cherche, toutes les heures.">
    <div class="flex flex-col gap-3.5">
      <p v-if="sourcesStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ sourcesStore.loadError }}
      </p>
      <UiSectionCard v-for="sourceCard in sourceCards" :key="sourceCard.status.source" class="gap-3">
        <span class="flex items-center gap-2.5">
          <span
            class="size-[9px] shrink-0 rounded-full"
            :class="[
              sourceCard.status.last_status
                ? SOURCE_RUN_STATUS_DOT_CLASSES[sourceCard.status.last_status]
                : 'bg-line-strong',
              { 'animate-pulse': sourceCard.button.isLoading },
            ]"
            aria-hidden="true"
          />
          <h2 class="m-0 font-display text-[22px] font-semibold">{{ sourceCard.status.label }}</h2>
        </span>
        <p class="m-0 text-[15px] text-ink-muted">{{ buildSourceStatusLine(sourceCard.status) }}</p>
        <p v-if="sourceCard.status.is_collected_by_desktop_app" class="m-0 text-sm text-ink-muted">
          Relevée par l’app Windows, quand un PC où elle tourne est allumé.
        </p>
        <p
          v-if="sourceCard.status.last_status === 'error' && sourceCard.status.error_message"
          class="m-0 text-sm text-coral-text"
        >
          {{ sourceCard.status.error_message }}
        </p>
        <p v-if="sourceCard.activityLine" class="m-0 text-sm font-bold text-ink-secondary" aria-live="polite">
          {{ sourceCard.activityLine }}
        </p>
        <p
          v-if="sourceCard.status.is_collected_by_desktop_app && centraleCanineRelayStore.lastRelayErrorMessage"
          class="m-0 text-sm text-coral-text"
        >
          Relais depuis ce PC en échec : {{ centraleCanineRelayStore.lastRelayErrorMessage }}
        </p>
        <p
          v-if="runErrorSource === sourceCard.status.source && runError"
          role="alert"
          class="m-0 text-sm font-bold text-coral-text"
        >
          {{ runError }}
        </p>
        <UButton
          v-if="sourceCard.status.is_collected"
          size="xl"
          class="mt-1 w-full justify-center md:w-auto md:self-start"
          :loading="sourceCard.button.isLoading"
          :disabled="sourceCard.button.isDisabled"
          @click="runNow(sourceCard.status)"
        >
          {{ sourceCard.button.label }}
        </UButton>
      </UiSectionCard>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type {
  CentraleCanineRelayAnswer,
  ListingSource,
  SourceActivity,
  SourceRunStatus,
  SourceStatus,
} from '~/types/api'
import type { AskedSourceRun, SourceRunCard, SourceRunContext, SourceRunEndNotice } from '~/types/SourceRun'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { SOURCE_RUN_COUNT_FORMS } from '~/constants/litterLabels'
import { SourcesService } from '~/services/sourcesService'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'
import { SourceRunPresentation } from '~/utils/sourceRunPresentation'

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

const askingSource: Ref<ListingSource | null> = ref(null)
const askedRuns: Ref<AskedSourceRun[]> = ref([])
const runError: Ref<string | null> = ref(null)
const runErrorSource: Ref<ListingSource | null> = ref(null)

const sourceRunContext: ComputedRef<SourceRunContext> = computed((): SourceRunContext => ({
  activity: sourcesStore.activity,
  isDesktopApp: isDesktopApp.value,
  isRelayingHere: centraleCanineRelayStore.isRelaying,
  relayProgressHere: centraleCanineRelayStore.relayProgress,
}))
const sourceCards: ComputedRef<SourceRunCard[]> = computed((): SourceRunCard[] =>
  sourcesStore.statuses.map((status: SourceStatus): SourceRunCard =>
    SourceRunPresentation.buildCard(status, sourceRunContext.value, askingSource.value === status.source),
  ),
)
const underWaySources: ComputedRef<ListingSource[]> = computed((): ListingSource[] =>
  sourceCards.value
    .filter((sourceCard: SourceRunCard): boolean => SourceRunPresentation.isUnderWay(sourceCard.phase))
    .map((sourceCard: SourceRunCard): ListingSource => sourceCard.status.source),
)

/**
 * Build the line under a source.
 *
 * @param status - The source status.
 * @returns « Relevé il y a 12 min · 19 portées vues », « … · 461 éleveurs vus », or why there is none.
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
  const [singularForm, pluralForm]: [string, string] = SOURCE_RUN_COUNT_FORMS[status.source]
  return `Relevé ${timeSinceRun} · ${seenCount} ${FrenchText.pickForm(seenCount, singularForm, pluralForm)}`
}

/**
 * Run a collection now: on the server, from this computer, or by asking a computer that is on. Every device then
 * sees it run, until it ends.
 *
 * @param status - The source status.
 */
async function runNow(status: SourceStatus): Promise<void> {
  askingSource.value = status.source
  runError.value = null
  runErrorSource.value = status.source
  try {
    if (status.is_collected_by_desktop_app && isDesktopApp.value) {
      await relayCentraleCanineNow()
      return
    }
    const askedRun: AskedSourceRun = SourceRunPresentation.recordAskedRun(status, sourcesStore.statuses)
    const activity: SourceActivity = status.is_collected_by_desktop_app
      ? await SourcesService.requestCentraleCanineRelay()
      : await SourcesService.run(status.source)
    sourcesStore.applyActivity(activity)
    askedRuns.value = [...askedRuns.value, askedRun]
  } catch (error: unknown) {
    runError.value = error instanceof Error ? error.message : 'Relevé impossible'
  } finally {
    askingSource.value = null
  }
}

/**
 * Relay the Centrale Canine from this computer now, every source in a row; the relay store refreshes the
 * statuses after the last run.
 */
async function relayCentraleCanineNow(): Promise<void> {
  if (centraleCanineRelayStore.isRelaying) {
    runError.value = 'Un relevé est déjà en cours depuis ce PC : il relève les sources à la suite.'
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
 * Tell this device that a relevé it asked is over: done, failed on some sources, or lost before it ran.
 *
 * @param askedRun - The relevé asked from this device.
 */
function announceRunEnd(askedRun: AskedSourceRun): void {
  const notice: SourceRunEndNotice = SourceRunPresentation.buildRunEndNotice(askedRun, sourcesStore.statuses)
  toast.add({ title: notice.title, color: notice.color })
}

watch(underWaySources, (sources: ListingSource[]): void => {
  const endedRuns: AskedSourceRun[] = askedRuns.value.filter(
    (askedRun: AskedSourceRun): boolean => !sources.includes(askedRun.source),
  )
  if (endedRuns.length === 0) {
    return
  }
  askedRuns.value = askedRuns.value.filter((askedRun: AskedSourceRun): boolean => sources.includes(askedRun.source))
  endedRuns.forEach((askedRun: AskedSourceRun): void => announceRunEnd(askedRun))
})

onMounted(async (): Promise<void> => {
  sourcesStore.startLiveUpdates()
  await sourcesStore.load()
})

onUnmounted((): void => {
  sourcesStore.stopLiveUpdates()
})
</script>
