<template>
  <section
    v-if="summary"
    class="flex items-center gap-4 rounded-card-compact p-4 md:gap-5 md:rounded-[24px] md:px-[22px] md:py-5"
    :class="summary.isGoldRuledOut ? 'bg-neutral-pastel' : 'bg-gold-pastel'"
  >
    <span
      class="flex size-20 shrink-0 flex-col items-center justify-center rounded-full bg-card md:size-24"
      :class="summary.isGoldRuledOut ? 'text-ink-secondary' : 'text-gold-ink'"
    >
      <span class="font-display text-[22px] leading-none font-bold md:text-[26px]">{{ summary.figure }}</span>
      <span class="text-[11px] font-extrabold md:text-xs">{{ summary.figureCaption }}</span>
    </span>
    <span class="flex min-w-0 flex-col gap-1">
      <h2 class="m-0 font-display text-lg leading-[1.2] font-semibold md:text-xl">Les chances de gold</h2>
      <p class="m-0 text-[15px] text-ink-secondary md:text-base">{{ summary.explanation }}</p>
    </span>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { GoldPuppyOddsSummary } from '~/types/GoldGenetics'
import type { LitterGoldOddsCardProps } from '~/types/LitterGoldOddsCard'
import { computed } from 'vue'
import { GoldGeneticsPresentation } from '~/utils/goldGeneticsPresentation'

const props: LitterGoldOddsCardProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const summary: ComputedRef<GoldPuppyOddsSummary | null> = computed((): GoldPuppyOddsSummary | null =>
  GoldGeneticsPresentation.buildPuppyOddsSummary(props.litter),
)
</script>
