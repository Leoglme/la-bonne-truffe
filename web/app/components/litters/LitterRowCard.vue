<template>
  <NuxtLink
    :to="`/portees/${props.litter.id}`"
    class="flex gap-3.5 rounded-card-compact bg-card p-3 text-ink no-underline shadow-card hover:text-ink"
  >
    <LitterTileFrame :litter="props.litter" class="size-[118px] rounded-tile-compact">
      <LitterVisual :litter="props.litter" :illustration-size-in-pixels="84" />
      <span
        class="absolute bottom-2 left-2 rounded-full bg-card px-[9px] py-[3px] text-[13px] leading-[1.45] font-extrabold text-coral-text"
      >
        {{ props.litter.score ?? '–' }} %
      </span>
    </LitterTileFrame>
    <span class="flex min-w-0 grow flex-col justify-center gap-1">
      <span class="flex items-center justify-between gap-1.5">
        <span class="truncate font-display text-lg leading-[1.2] font-semibold">{{ props.litter.name }}</span>
        <span
          v-if="props.isNew"
          class="inline-flex shrink-0 rounded-full bg-coral px-2 py-[3px] text-[11px] leading-[1.45] font-extrabold text-white"
        >
          Nouveau
        </span>
      </span>
      <span class="text-[13px] text-ink-muted">{{ LitterPresentation.placeLine(props.litter) }}</span>
      <span class="mt-0.5 flex items-center gap-1.5 text-[13px] font-bold text-ink-secondary">
        <span class="rounded-full bg-chip px-[9px] py-[3px]">
          {{ LitterPresentation.colorLabel(props.litter.colors, true) }}
        </span>
        <span>{{ LitterPresentation.sexLine(props.litter) }}</span>
      </span>
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterRowCardProps } from '~/types/LitterRowCard'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Litter card of the iPhone list: the tile on the left, name, place, colour and sexes on the right. */
const props: LitterRowCardProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
  isNew: { type: Boolean, default: false },
})
</script>
