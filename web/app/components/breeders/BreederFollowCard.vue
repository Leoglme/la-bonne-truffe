<template>
  <section
    class="flex flex-col gap-2.5"
    :class="
      props.isInSidePanel
        ? 'rounded-[18px] bg-cream p-3.5'
        : 'rounded-[20px] bg-card p-4 shadow-card md:rounded-card-compact md:px-[22px] md:py-5'
    "
  >
    <div class="flex items-center justify-between gap-3">
      <h2 class="m-0 font-display font-semibold" :class="props.isInSidePanel ? 'text-base' : 'text-lg md:text-xl'">
        Mon suivi
      </h2>
      <span
        v-if="props.breeder.follow"
        class="inline-flex shrink-0 rounded-full bg-coral-pastel px-2.5 py-1 text-xs font-extrabold whitespace-nowrap text-coral-text md:px-3 md:text-[13px]"
      >
        {{ BREEDER_FOLLOW_STATUS_LABELS[props.breeder.follow.status] }}
      </span>
    </div>
    <template v-if="props.breeder.follow">
      <p v-if="props.breeder.follow.notes.length === 0" class="m-0 text-sm text-ink-muted md:text-[15px]">
        Pas encore de note. Après un appel, écris ce qu’il t’a dit.
      </p>
      <ul v-else class="m-0 flex list-none flex-col gap-2 p-0">
        <li v-for="note in shownNotes" :key="note.id" class="text-sm leading-[1.45] text-ink-secondary md:text-[15px]">
          <span class="font-extrabold text-ink-label"
            >{{ FrenchDate.formatApiDayAndShortMonth(note.created_at) }} · </span
          >{{ note.text }}
        </li>
      </ul>
      <span
        v-if="reminderLabel"
        class="inline-flex items-center gap-1.5 self-start rounded-full bg-chip px-3 py-1.5 text-[13px] font-extrabold text-ink-secondary md:text-[15px]"
      >
        <UIcon name="i-lucide-bell-ring" class="size-4 shrink-0 text-coral" />
        {{ reminderLabel }}
      </span>
      <button
        type="button"
        aria-haspopup="dialog"
        class="min-h-11 self-start border-0 bg-transparent px-0 text-[15px] font-extrabold text-coral-text"
        @click="breederFollowStore.openWith(props.breeder)"
      >
        Modifier le suivi
      </button>
    </template>
    <template v-else>
      <p class="m-0 text-sm text-ink-muted md:text-[15px]">
        Suis cet élevage pour être prévenu de ses saillies et de ses naissances, et noter tes échanges.
      </p>
      <button
        type="button"
        aria-haspopup="dialog"
        class="inline-flex min-h-11 items-center gap-1.5 self-start border-0 bg-transparent px-0 text-[15px] font-extrabold text-coral-text"
        @click="breederFollowStore.openWith(props.breeder)"
      >
        <UiCustomIcon name="heart" :size-in-pixels="18" :stroke-width="2.2" />
        Suivre cet élevage
      </button>
    </template>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederDetail, BreederFollowNote } from '~/types/api'
import type { BreederDetailSectionProps } from '~/types/BreederDetailSection'
import { computed } from 'vue'
import { BREEDER_FOLLOW_STATUS_LABELS } from '~/constants/breederOptions'
import { BreederPresentation } from '~/utils/breederPresentation'
import { FrenchDate } from '~/utils/frenchDate'

const SHOWN_NOTES_COUNT: number = 3

const props: BreederDetailSectionProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const breederFollowStore: ReturnType<typeof useBreederFollowStore> = useBreederFollowStore()

const shownNotes: ComputedRef<BreederFollowNote[]> = computed((): BreederFollowNote[] =>
  (props.breeder.follow?.notes ?? []).slice(0, props.isInSidePanel ? 1 : SHOWN_NOTES_COUNT),
)
const reminderLabel: ComputedRef<string | null> = computed((): string | null =>
  props.breeder.follow && !props.isInSidePanel ? BreederPresentation.buildReminderLabel(props.breeder.follow) : null,
)
</script>
