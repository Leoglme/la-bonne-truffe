<template>
  <span
    class="relative box-border flex shrink-0 items-center justify-center"
    :class="props.litter.kind === 'litter_expected' ? 'border-[3px] border-dashed border-coral-text/35' : ''"
    :style="{ backgroundColor: tileColor }"
  >
    <slot />
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterTileFrameProps } from '~/types/LitterTileFrame'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Pastel tile of a litter, coloured by its coat; a litter to be born gets the dashed coral border. */
const props: LitterTileFrameProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
})

const tileColor: ComputedRef<string> = computed(
  (): string => COCKER_COAT_PALETTES[LitterPresentation.coatOf(props.litter.colors)].tile,
)
</script>
