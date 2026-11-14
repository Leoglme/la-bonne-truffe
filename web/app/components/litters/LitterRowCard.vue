<template>
  <NuxtLink
    :to="`/portees/${props.litter.id}`"
    class="flex gap-3.5 rounded-card-compact bg-card p-3 text-ink no-underline shadow-card hover:text-ink"
  >
    <LitterTileFrame :litter="props.litter" class="size-[118px] rounded-tile-compact">
      <LitterVisual
        :litter="props.litter"
        :illustration-size-in-pixels="84"
        photo-source-label-class="top-2 left-2 px-2 py-0.5 text-[11px]"
      />
      <span
        class="absolute bottom-2 left-2 rounded-full bg-card px-[9px] py-[3px] text-[13px] leading-[1.45] font-extrabold text-coral-text"
      >
        {{ props.litter.score ?? '–' }} %
      </span>
    </LitterTileFrame>
    <span class="flex min-w-0 grow flex-col justify-center gap-1">
      <span class="flex items-center justify-between gap-1.5">
        <span class="truncate font-display text-lg leading-[1.2] font-semibold">{{ rowTitle }}</span>
        <span
          v-if="props.isNew"
          class="inline-flex shrink-0 rounded-full bg-coral px-2 py-[3px] text-[11px] leading-[1.45] font-extrabold text-white"
        >
          Nouveau
        </span>
      </span>
      <span v-if="rowSubtitle" class="text-[13px] text-ink-muted">{{ rowSubtitle }}</span>
      <span class="mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-[13px] font-bold text-ink-secondary">
        <span class="max-w-full rounded-full bg-chip px-[9px] py-[3px]">
          {{ LitterPresentation.buildColorLabel(props.litter.colors, true) }}
        </span>
        <LitterSexCounts :litter="props.litter" class="whitespace-nowrap" />
      </span>
      <span v-if="goldPuppyOddsLine" class="text-[13px] font-bold text-balance text-gold-ink">
        {{ goldPuppyOddsLine }}
      </span>
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterRowCardProps } from '~/types/LitterRowCard'
import { computed } from 'vue'
import { GoldGeneticsPresentation } from '~/utils/goldGeneticsPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterRowCardProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
  isNew: { type: Boolean, default: false },
  drivingMinutes: { type: Number as PropType<number | null>, default: null },
  isGoldPuppyOddsShown: { type: Boolean, default: false },
  isAmongBreederLitters: { type: Boolean, default: false },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const rowTitle: ComputedRef<string> = computed((): string =>
  props.isAmongBreederLitters ? LitterPresentation.buildBreederRowTitle(props.litter) : props.litter.name,
)
const rowSubtitle: ComputedRef<string | null> = computed((): string | null =>
  props.isAmongBreederLitters
    ? LitterPresentation.buildBreederRowSubtitle(props.litter)
    : LitterPresentation.buildPlaceLine(props.litter, locationStore.position, props.drivingMinutes),
)
const goldPuppyOddsLine: ComputedRef<string | null> = computed((): string | null =>
  props.isGoldPuppyOddsShown ? GoldGeneticsPresentation.buildPuppyOddsLine(props.litter.gold_puppy_odds ?? null) : null,
)
</script>
