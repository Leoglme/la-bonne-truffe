<template>
  <span
    class="inline-flex h-10 items-center gap-1.5 rounded-full border-[3px] bg-card ps-0.5 pe-3 text-[13px] leading-none font-extrabold whitespace-nowrap shadow-map-pin group-focus-visible:outline-3 group-focus-visible:outline-offset-2 group-focus-visible:outline-coral"
    :class="props.isSelected ? 'border-coral' : 'border-card'"
  >
    <template v-if="singleLitter">
      <span
        class="relative flex size-[26px] shrink-0 items-center justify-center overflow-hidden rounded-full"
        :class="LitterPresentation.resolveTileClass(singleLitter.colors)"
      >
        <LitterVisual :litter="singleLitter" :illustration-size-in-pixels="24" />
      </span>
      <span class="text-coral-text">{{ LitterMapPlaces.buildScoreLabel(singleLitter) }}</span>
    </template>
    <template v-else>
      <span
        class="inline-flex size-[26px] shrink-0 items-center justify-center rounded-full bg-coral-pastel text-xs text-coral-text"
      >
        {{ props.litters.length }}
      </span>
      <span class="text-ink-secondary">portées</span>
    </template>
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterMapPinProps } from '~/types/LitterMapPin'
import { computed } from 'vue'
import { LitterMapPlaces } from '~/utils/litterMapPlaces'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterMapPinProps = defineProps({
  litters: { type: Array as PropType<LitterCard[]>, required: true },
  isSelected: { type: Boolean, default: false },
})

const singleLitter: ComputedRef<LitterCard | null> = computed((): LitterCard | null =>
  props.litters.length === 1 ? (props.litters[0] ?? null) : null,
)
</script>
