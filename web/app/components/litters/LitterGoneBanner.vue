<template>
  <p
    v-if="goneSinceLabel"
    role="status"
    class="m-0 shrink-0 rounded-2xl bg-coral-pastel px-4 py-3 font-bold text-coral-text"
    :class="props.isInSidePanel ? 'text-sm' : 'text-[15px] md:text-base'"
  >
    {{ goneSinceLabel }} : la portée a disparu de ses sources.
  </p>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterGoneBannerProps } from '~/types/LitterGoneBanner'
import { computed } from 'vue'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterGoneBannerProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const goneSinceLabel: ComputedRef<string | null> = computed((): string | null =>
  LitterPresentation.buildGoneSinceLabel(props.litter),
)
</script>
