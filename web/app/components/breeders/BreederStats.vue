<template>
  <dl class="m-0 grid grid-cols-3 gap-2 md:gap-3">
    <div
      v-for="stat in stats"
      :key="stat.label"
      class="flex flex-col gap-0.5"
      :class="
        props.isInAside
          ? 'rounded-2xl bg-cream px-3 py-2.5'
          : 'rounded-[18px] bg-card p-3 shadow-card md:rounded-[22px] md:px-[18px] md:py-4'
      "
    >
      <dt class="text-[11px] font-extrabold tracking-[0.04em] text-ink-label uppercase md:text-[13px]">
        <span :class="props.isInAside ? '' : 'md:hidden'">{{ stat.compactLabel }}</span>
        <span v-if="!props.isInAside" class="hidden md:inline">{{ stat.label }}</span>
      </dt>
      <dd class="m-0 font-display font-semibold" :class="props.isInAside ? 'text-[17px]' : 'text-lg md:text-[22px]'">
        {{ stat.value }}
      </dd>
    </div>
  </dl>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederStat } from '~/types/Breeder'
import type { BreederStatsProps } from '~/types/BreederStats'
import { computed } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederStatsProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
  isInAside: { type: Boolean, default: false },
})

const stats: ComputedRef<BreederStat[]> = computed((): BreederStat[] => BreederPresentation.buildStats(props.breeder))
</script>
