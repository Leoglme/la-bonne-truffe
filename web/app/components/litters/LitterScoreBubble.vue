<template>
  <span
    class="flex size-16 shrink-0 flex-col items-center justify-center rounded-full bg-coral-pastel text-coral-text md:size-[84px]"
  >
    <span class="font-display text-xl leading-none font-bold md:text-[28px]">{{ props.litter.score ?? '–' }} %</span>
    <span class="text-[10px] font-extrabold md:text-xs">
      {{ props.litter.tier ? TIER_LABELS[props.litter.tier] : UNEVALUATED_TIER_LABEL }}
    </span>
  </span>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterScoreBubbleProps } from '~/types/LitterScoreBubble'
import { TIER_LABELS, UNEVALUATED_TIER_LABEL } from '~/constants/litterLabels'

const props: LitterScoreBubbleProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})
</script>
