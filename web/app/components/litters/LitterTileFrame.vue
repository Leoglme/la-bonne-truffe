<template>
  <span
    class="relative box-border flex shrink-0 items-center justify-center"
    :class="[
      LitterPresentation.resolveTileClass(props.litter.colors),
      props.litter.kind === 'litter_expected' ? 'border-[3px] border-dashed border-coral-text/35' : '',
    ]"
  >
    <slot />
  </span>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterTileFrameProps } from '~/types/LitterTileFrame'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterTileFrameProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
})
</script>
