<template>
  <UiTabScreen title="Sources" subtitle="Où la truffe cherche, toutes les heures.">
    <div class="flex flex-col gap-3.5">
      <p v-if="sourcesStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ sourcesStore.loadError }}
      </p>
      <p v-if="runError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">{{ runError }}</p>
      <UiSectionCard v-for="status in sourcesStore.statuses" :key="status.source" class="gap-3">
        <div class="flex items-center justify-between gap-3">
          <span class="flex items-center gap-2.5">
            <span
              class="size-[9px] shrink-0 rounded-full"
              :class="status.last_status ? SOURCE_RUN_STATUS_DOT_CLASSES[status.last_status] : 'bg-line-strong'"
              aria-hidden="true"
            />
            <h2 class="m-0 font-display text-[22px] font-semibold">{{ status.label }}</h2>
          </span>
          <UButton
            v-if="status.is_collected"
            color="neutral"
            variant="outline"
            class="shrink-0"
            :disabled="runningSource !== null"
            @click="runNow(status.source)"
          >
            {{ runningSource === status.source ? 'Relevé en cours…' : 'Relever maintenant' }}
          </UButton>
        </div>
        <p class="m-0 text-[15px] text-ink-muted">{{ buildSourceStatusLine(status) }}</p>
        <p v-if="status.last_status === 'error' && status.error_message" class="m-0 text-sm text-coral-text">
          {{ status.error_message }}
        </p>
      </UiSectionCard>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { ListingSource, SourceRunStatus, SourceStatus } from '~/types/api'
import { onMounted, ref } from 'vue'
import { SourcesService } from '~/services/sourcesService'
import { FrenchDate } from '~/utils/frenchDate'
import { FrenchText } from '~/utils/frenchText'

useHead({ title: 'Sources · La Bonne Truffe' })

const sourcesStore: ReturnType<typeof useSourcesStore> = useSourcesStore()

const SOURCE_RUN_STATUS_DOT_CLASSES: Record<SourceRunStatus, string> = {
  ok: 'bg-online',
  error: 'bg-coral-text',
  running: 'bg-line-strong',
}

const runningSource: Ref<ListingSource | null> = ref(null)
const runError: Ref<string | null> = ref(null)

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

  if (status.last_status === 'error') {
    return `Dernier relevé en échec, ${timeSinceRun}.`
  }
  const seenCount: number = status.listings_seen ?? 0
  return `Relevé ${timeSinceRun} · ${seenCount} ${FrenchText.pickForm(seenCount, 'portée vue', 'portées vues')}`
}

/**
 * Run a collection now and refresh the statuses.
 *
 * @param source - The source.
 */
async function runNow(source: ListingSource): Promise<void> {
  runningSource.value = source
  runError.value = null
  try {
    sourcesStore.statuses = await SourcesService.run(source)
  } catch (error: unknown) {
    runError.value = error instanceof Error ? error.message : 'Relevé impossible'
  } finally {
    runningSource.value = null
  }
}

onMounted((): Promise<void> => sourcesStore.load())
</script>
