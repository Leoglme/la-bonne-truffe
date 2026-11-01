<template>
  <div
    v-if="props.litter.reasons.length > 0"
    class="flex flex-col gap-2 rounded-[20px] bg-card px-4 py-3.5 shadow-card md:gap-3 md:rounded-card-compact md:px-[22px] md:py-5"
  >
    <h2 class="m-0 font-display text-[17px] font-semibold md:text-xl">Pourquoi {{ props.litter.score }} %</h2>
    <ul class="m-0 flex list-none flex-col gap-1.5 p-0 text-sm md:gap-2.5 md:text-base">
      <li
        v-for="(reason, reasonIndex) in shownReasons"
        :key="reason.text"
        class="items-center gap-2.5 md:gap-3"
        :class="reasonIndex >= PHONE_REASON_LINE_LIMIT ? 'hidden md:flex' : 'flex'"
      >
        <span
          class="inline-flex size-[22px] shrink-0 items-center justify-center rounded-full bg-coral-pastel text-coral-text md:size-[26px]"
        >
          <UIcon name="i-lucide-check" class="size-3 md:size-3.5" />
        </span>
        {{ reason.text }}
      </li>
    </ul>
    <p v-if="factsToConfirmLine" class="m-0 mt-1 text-sm text-ink-muted md:text-base">
      {{ factsToConfirmLine }}
    </p>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail, LitterReason } from '~/types/api'
import type { LitterReasonsCardProps } from '~/types/LitterReasonsCard'
import { computed } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterReasonsCardProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const REASON_LINE_LIMIT: number = 5
const PHONE_REASON_LINE_LIMIT: number = 3

const shownReasons: ComputedRef<LitterReason[]> = computed((): LitterReason[] =>
  [...props.litter.reasons]
    .sort((first: LitterReason, second: LitterReason): number => second.points - first.points)
    .slice(0, REASON_LINE_LIMIT),
)
const factsToConfirmLine: ComputedRef<string | null> = computed((): string | null =>
  LitterDetailPresentation.buildFactsToConfirmLine(props.litter),
)
</script>
