<template>
  <div class="grid grid-cols-3" :class="props.variant === 'panel' ? 'gap-2' : 'gap-2 md:gap-3'">
    <div
      v-for="fact in keyFacts"
      :key="fact.label"
      class="flex flex-col"
      :class="
        props.variant === 'panel'
          ? 'rounded-2xl bg-cream px-3 py-2.5'
          : 'rounded-2xl bg-card px-3 py-2.5 shadow-card md:gap-0.5 md:rounded-[22px] md:px-[18px] md:py-4'
      "
    >
      <span
        class="font-extrabold text-ink-label uppercase"
        :class="props.variant === 'panel' ? 'text-[11px]' : 'text-[11px] md:text-[13px] md:tracking-[0.04em]'"
      >
        {{ fact.label }}
      </span>
      <span
        class="font-display font-semibold"
        :class="props.variant === 'panel' ? 'text-[17px]' : 'text-base md:text-[22px]'"
      >
        <template v-if="props.variant === 'panel'">{{ fact.compactValue }}</template>
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
import type { LitterDetailVariant } from '~/types/LitterDetailVariant'
import type { LitterKeyFactsProps } from '~/types/LitterKeyFacts'
import type { LitterKeyFact } from '~/utils/litterDetailPresentation'
import { computed } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

/** The three key facts of a litter: birth, puppies, departure. */
const props: LitterKeyFactsProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  variant: { type: String as PropType<LitterDetailVariant>, default: 'responsive' },
})

const keyFacts: ComputedRef<LitterKeyFact[]> = computed((): LitterKeyFact[] =>
  LitterDetailPresentation.keyFacts(props.litter),
)
</script>
