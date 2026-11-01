<template>
  <section
    v-if="slices.length > 0"
    class="flex flex-col gap-3 rounded-[20px] bg-card p-4 shadow-card md:rounded-card-compact md:px-[22px] md:py-5"
  >
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="m-0 font-display text-lg font-semibold md:text-xl">Ses couleurs</h2>
      <span class="text-xs text-ink-label md:text-sm">{{ littersCountLabel }}</span>
    </div>
    <span role="img" :aria-label="barDescription" class="flex h-3 gap-[3px] overflow-hidden rounded-full md:h-4">
      <span
        v-for="slice in slices"
        :key="slice.label"
        class="h-full rounded-full"
        :style="{ width: `${slice.percent}%`, backgroundColor: slice.swatch }"
      />
    </span>
    <ul class="m-0 flex list-none flex-wrap gap-x-4 gap-y-1.5 p-0 text-[13px] text-ink-secondary md:text-sm">
      <li v-for="slice in slices" :key="slice.label" class="inline-flex items-center gap-1.5">
        <span class="size-2.5 rounded-full md:size-3" :style="{ backgroundColor: slice.swatch }" aria-hidden="true" />
        {{ slice.label }} · {{ slice.littersCount }}
      </li>
    </ul>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederColorShareSlice } from '~/types/Breeder'
import type { BreederDetailSectionProps } from '~/types/BreederDetailSection'
import { computed } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'
import { FrenchText } from '~/utils/frenchText'

const props: BreederDetailSectionProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
})

const slices: ComputedRef<BreederColorShareSlice[]> = computed((): BreederColorShareSlice[] =>
  BreederPresentation.buildColorShares(props.breeder),
)
const littersCountLabel: ComputedRef<string> = computed((): string => {
  const count: number = props.breeder.litters_count
  return `${count} ${FrenchText.pickForm(count, 'portée connue', 'portées connues')}`
})
const barDescription: ComputedRef<string> = computed((): string =>
  slices.value.map((slice: BreederColorShareSlice): string => `${slice.label} ${slice.percent} %`).join(', '),
)
</script>
