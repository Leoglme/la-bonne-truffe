<template>
  <UiTabScreen title="Sources" subtitle="Où la truffe cherche, toutes les heures.">
    <div class="flex flex-col gap-3.5">
      <p v-if="runError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">{{ runError }}</p>
      <section
        v-for="status in sourcesStore.statuses"
        :key="status.source"
        class="flex flex-col gap-3 rounded-[26px] bg-card px-[22px] py-5 shadow-card"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="flex items-center gap-2.5">
            <span class="size-[9px] shrink-0 rounded-full" :class="dotClass(status)" aria-hidden="true" />
            <h2 class="m-0 font-display text-[22px] font-semibold">{{ status.label }}</h2>
          </span>
          <button
            v-if="status.is_collected"
            type="button"
            class="box-content min-h-11 shrink-0 rounded-full border-2 border-ink bg-transparent px-[18px] text-[15px] font-extrabold text-ink disabled:opacity-60"
            :disabled="runningSource !== null"
            @click="runNow(status.source)"
          >
            {{ runningSource === status.source ? 'Relevé en cours…' : 'Relever maintenant' }}
          </button>
        </div>
        <p class="m-0 text-[15px] text-ink-muted">{{ statusLine(status) }}</p>
        <p v-if="status.last_status === 'error' && status.error_message" class="m-0 text-sm text-coral-text">
          {{ status.error_message }}
        </p>
      </section>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { ListingSource, SourceStatus } from '~/types/api'
import { onMounted, ref } from 'vue'
import { SourcesService } from '~/services/sourcesService'
import { RelativeTime } from '~/utils/relativeTime'

useHead({ title: 'Sources · La Bonne Truffe' })

const sourcesStore: ReturnType<typeof useSourcesStore> = useSourcesStore()

const runningSource: Ref<ListingSource | null> = ref(null)
const runError: Ref<string | null> = ref(null)

/**
 * Colour of the status dot: green when the last run succeeded, coral when it failed, grey otherwise.
 *
 * @param status - The source status.
 * @returns The Tailwind class.
 */
function dotClass(status: SourceStatus): string {
  if (status.last_status === 'ok') {
    return 'bg-online'
  }
  return status.last_status === 'error' ? 'bg-coral-text' : 'bg-line-strong'
}

/**
 * The line under a source.
 *
 * @param status - The source status.
 * @returns « Relevé il y a 12 min · 19 portées vues », or why there is none.
 */
function statusLine(status: SourceStatus): string {
  if (!status.is_collected) {
    return 'Pas encore relevée.'
  }
  if (status.last_run_at === null) {
    return 'Aucun relevé pour l’instant.'
  }
  const when: string = RelativeTime.since(new Date(`${status.last_run_at}Z`), new Date())
  if (status.last_status === 'error') {
    return `Dernier relevé en échec, ${when}.`
  }
  const seen: number = status.listings_seen ?? 0
  return `Relevé ${when} · ${seen} portée${seen > 1 ? 's' : ''} vue${seen > 1 ? 's' : ''}`
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

onMounted((): void => {
  void sourcesStore.load()
})
</script>
