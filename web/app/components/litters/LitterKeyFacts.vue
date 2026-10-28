<template>
  <div class="grid grid-cols-3" :class="props.isInSidePanel ? 'gap-2' : 'gap-2 md:gap-3'">
    <div
      v-for="fact in keyFacts"
      :key="fact.key"
      class="flex flex-col"
      :class="
        props.isInSidePanel
          ? 'rounded-2xl bg-cream px-3 py-2.5'
          : 'rounded-2xl bg-card px-3 py-2.5 shadow-card md:gap-0.5 md:rounded-[22px] md:px-[18px] md:py-4'
      "
    >
      <span
        class="font-extrabold text-ink-label uppercase"
        :class="props.isInSidePanel ? 'text-[11px]' : 'text-[11px] md:text-[13px] md:tracking-[0.04em]'"
      >
        {{ fact.label }}
      </span>
      <span
        class="font-display font-semibold"
        :class="props.isInSidePanel ? 'text-[17px]' : 'text-base md:text-[22px]'"
      >
        <LitterSexCounts v-if="fact.key === 'puppies'" :litter="props.litter" />
        <template v-else-if="props.isInSidePanel">{{ fact.compactValue }}</template>
        <template v-else>
          <span class="md:hidden">{{ fact.compactValue }}</span>
          <span class="hidden md:inline">{{ fact.value }}</span>
        </template>
      </span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterKeyFact } from '~/types/Litter'
import type { LitterKeyFactsProps } from '~/types/LitterKeyFacts'
import { computed } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterKeyFactsProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const keyFacts: ComputedRef<LitterKeyFact[]> = computed((): LitterKeyFact[] =>
  LitterDetailPresentation.buildKeyFacts(props.litter),
)
</script>
