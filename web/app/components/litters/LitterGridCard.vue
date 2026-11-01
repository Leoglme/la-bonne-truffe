<template>
  <NuxtLink
    :to="`/portees/${props.litter.id}`"
    class="flex flex-col gap-3 rounded-card bg-card px-3.5 pt-3.5 pb-[18px] text-ink no-underline shadow-card hover:text-ink lg:gap-2.5 lg:rounded-[26px]"
  >
    <LitterTileFrame :litter="props.litter" class="h-[200px] rounded-tile lg:h-[170px] lg:rounded-[20px]">
      <LitterVisual :litter="props.litter" :illustration-size-in-pixels="132" illustration-class="lg:size-[110px]" />
      <span
        class="absolute top-3.5 left-3.5 rounded-full bg-card px-3 py-[5px] text-[15px] leading-normal font-extrabold text-coral-text lg:top-3 lg:left-3 lg:px-[11px] lg:py-1 lg:text-sm"
      >
        {{ props.litter.score ?? '–' }} %
      </span>
      <span
        v-if="props.isNew"
        class="absolute top-3.5 right-3.5 inline-flex rounded-full bg-coral px-3 py-[5px] text-[13px] leading-normal font-extrabold text-white lg:top-3 lg:right-3 lg:px-[11px] lg:py-1 lg:text-xs"
      >
        Nouveau
      </span>
    </LitterTileFrame>
    <span class="flex flex-col gap-0.5 px-1.5">
      <span class="font-display text-[21px] leading-[1.2] font-semibold lg:text-[19px]">{{ props.litter.name }}</span>
      <span class="text-[15px] text-ink-muted lg:text-sm">
        {{ LitterPresentation.buildPlaceLine(props.litter, locationStore.position) }}
      </span>
    </span>
    <span
      class="flex flex-wrap items-center gap-x-2 gap-y-1.5 px-1.5 text-[15px] font-bold text-ink-secondary lg:text-sm"
    >
      <span class="max-w-full rounded-full bg-chip px-2.5 py-1 lg:px-[9px] lg:py-[3px]">
        <span class="lg:hidden">{{ LitterPresentation.buildColorLabel(props.litter.colors, false) }}</span>
        <span class="hidden lg:inline">{{ LitterPresentation.buildColorLabel(props.litter.colors, true) }}</span>
      </span>
      <LitterSexCounts :litter="props.litter" class="whitespace-nowrap" />
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterGridCardProps } from '~/types/LitterGridCard'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterGridCardProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
  isNew: { type: Boolean, default: false },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()
</script>
