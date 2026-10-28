<template>
  <span
    class="flex shrink-0 flex-col items-center justify-center rounded-full bg-coral-pastel text-coral-text"
    :class="props.isInSidePanel ? 'size-[70px]' : 'size-16 md:size-[84px]'"
  >
    <span
      class="font-display leading-none font-bold"
      :class="props.isInSidePanel ? 'text-[22px]' : 'text-xl md:text-[28px]'"
    >
      {{ props.litter.score ?? '–' }} %
    </span>
    <span class="font-extrabold" :class="props.isInSidePanel ? 'text-[11px]' : 'text-[10px] md:text-xs'">
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
  isInSidePanel: { type: Boolean, default: false },
})
</script>
