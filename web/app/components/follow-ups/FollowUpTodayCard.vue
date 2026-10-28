<template>
  <button
    type="button"
    class="flex w-full items-center gap-3.5 rounded-card-compact border-0 bg-coral-pastel p-[18px] text-left text-ink md:gap-[18px] md:rounded-[26px] md:px-6 md:py-[22px]"
    @click="emit('open', props.followUp.litter.id)"
  >
    <span class="inline-flex size-11 shrink-0 items-center justify-center rounded-full bg-card text-coral md:size-14">
      <UiMockupIcon name="phone" :size-in-pixels="26" :stroke-width="2.2" class="size-[22px] md:size-[26px]" />
    </span>
    <span class="flex min-w-0 grow flex-col gap-0.5">
      <span class="text-xs font-extrabold tracking-[0.04em] text-coral-text md:text-[13px]">AUJOURD’HUI</span>
      <span class="font-display text-lg leading-[1.2] font-semibold md:text-[22px]"
        >Appeler {{ props.followUp.litter.name }}</span
      >
      <span class="text-sm text-ink-secondary md:text-[15px]">{{ description }}</span>
    </span>
    <UiMockupIcon name="chevron-right" :size-in-pixels="22" :stroke-width="2.4" class="shrink-0 text-coral-text" />
  </button>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { FollowUpCard } from '~/types/api'
import type { FollowUpTodayCardEmits, FollowUpTodayCardProps } from '~/types/FollowUpTodayCard'
import { computed } from 'vue'
import { FollowUpPresentation } from '~/utils/followUpPresentation'

/** « Aujourd’hui : appeler… », the reminder of the day at the top of the follow-up screen. */
const props: FollowUpTodayCardProps = defineProps({
  followUp: { type: Object as PropType<FollowUpCard>, required: true },
})

const emit: FollowUpTodayCardEmits = defineEmits<{
  (event: 'open', litterId: number): void
}>()

const description: ComputedRef<string> = computed(
  (): string => props.followUp.last_note?.text ?? FollowUpPresentation.summaryLine(props.followUp),
)
</script>
