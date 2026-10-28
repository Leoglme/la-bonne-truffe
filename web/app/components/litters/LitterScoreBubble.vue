<template>
  <span
    class="flex shrink-0 flex-col items-center justify-center rounded-full bg-coral-pastel text-coral-text"
    :class="props.variant === 'panel' ? 'size-[70px]' : 'size-16 md:size-[84px]'"
  >
    <span
      class="font-display leading-none font-bold"
      :class="props.variant === 'panel' ? 'text-[22px]' : 'text-xl md:text-[28px]'"
    >
      {{ props.litter.score ?? '–' }} %
    </span>
    <span class="font-extrabold" :class="props.variant === 'panel' ? 'text-[11px]' : 'text-[10px] md:text-xs'">
      {{ LitterDetailPresentation.tierLabel(props.litter) }}
    </span>
  </span>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterDetailVariant } from '~/types/LitterDetailVariant'
import type { LitterScoreBubbleProps } from '~/types/LitterScoreBubble'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

/** Round score bubble with the tier under it (« 96 % préférée »). */
const props: LitterScoreBubbleProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  variant: { type: String as PropType<LitterDetailVariant>, default: 'responsive' },
})
</script>
