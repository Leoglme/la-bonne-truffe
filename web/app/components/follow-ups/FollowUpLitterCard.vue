<template>
  <button
    type="button"
    class="flex w-full flex-col gap-3 rounded-card-compact border-0 bg-card p-3 text-left text-ink shadow-card md:py-3.5 md:pr-[18px] md:pl-3.5"
    :class="props.isNoteShown && props.followUp.last_note ? 'pb-4' : ''"
    @click="emit('open', props.followUp.litter.id)"
  >
    <span class="flex w-full items-center gap-3.5 md:gap-4">
      <LitterTileFrame
        :litter="props.followUp.litter"
        class="size-16 rounded-tile-compact md:size-[72px] md:rounded-[20px]"
      >
        <LitterVisual :litter="props.followUp.litter" :illustration-size-in-pixels="52" />
      </LitterTileFrame>
      <span class="flex min-w-0 grow flex-col gap-0.5">
        <span class="font-display text-lg leading-[1.2] font-semibold md:text-[21px] md:leading-normal">
          {{ props.followUp.litter.name }}
        </span>
        <span class="text-[13px] text-ink-muted md:text-[15px]">{{
          FollowUpPresentation.buildSummaryLine(props.followUp)
        }}</span>
        <span
          v-if="reminderChip"
          class="mt-1 self-start rounded-full px-2.5 py-1 text-xs font-extrabold whitespace-nowrap md:hidden"
          :class="reminderChip.isUrgent ? 'bg-coral text-white' : 'bg-chip text-ink-secondary'"
        >
          {{ reminderChip.label }}
        </span>
      </span>
      <span
        v-if="reminderChip"
        class="hidden rounded-full px-3 py-1.5 text-[13px] font-extrabold whitespace-nowrap md:inline"
        :class="reminderChip.isUrgent ? 'bg-coral text-white' : 'bg-chip text-ink-secondary'"
      >
        {{ reminderChip.label }}
      </span>
    </span>
    <span
      v-if="props.isNoteShown && props.followUp.last_note"
      class="w-full rounded-[14px] bg-cream px-3.5 py-2.5 text-sm leading-[1.45] text-ink-secondary md:text-[15px]"
    >
      {{ props.followUp.last_note.text }}
    </span>
  </button>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { FollowUpCard } from '~/types/api'
import type { FollowUpReminderChip } from '~/types/FollowUp'
import type { FollowUpLitterCardEmits, FollowUpLitterCardProps } from '~/types/FollowUpLitterCard'
import { computed } from 'vue'
import { FollowUpPresentation } from '~/utils/followUpPresentation'

const props: FollowUpLitterCardProps = defineProps({
  followUp: { type: Object as PropType<FollowUpCard>, required: true },
  isNoteShown: { type: Boolean, default: false },
})

const emit: FollowUpLitterCardEmits = defineEmits<{
  (event: 'open', litterId: number): void
}>()

const reminderChip: ComputedRef<FollowUpReminderChip | null> = computed((): FollowUpReminderChip | null =>
  FollowUpPresentation.buildReminderChip(props.followUp, new Date()),
)
</script>
