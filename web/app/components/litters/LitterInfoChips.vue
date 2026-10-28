<template>
  <div class="flex flex-wrap" :class="props.isInSidePanel ? 'gap-2' : 'gap-2 md:gap-2.5'">
    <span
      class="inline-flex items-center rounded-full font-extrabold"
      :class="[chipSizeClass, coatPalette.tileClass, coatPalette.chipTextClass]"
    >
      <span
        class="shrink-0 rounded-full"
        :class="props.isInSidePanel ? 'size-2.5' : 'size-2.5 md:size-3'"
        :style="{ backgroundColor: coatPalette.coat }"
        aria-hidden="true"
      />
      {{ LitterPresentation.buildColorLabel(props.litter.colors, true) }}
    </span>
    <span
      class="rounded-full"
      :class="[
        chipSizeClass,
        props.litter.lof_status === 'lof' ? 'bg-lof-pastel text-lof-ink' : 'bg-chip text-ink-secondary',
      ]"
    >
      {{ LOF_STATUS_LABELS[props.litter.lof_status] }}
    </span>
    <span v-if="props.litter.breeder?.has_affix" class="rounded-full bg-chip text-ink-secondary" :class="chipSizeClass">
      <template v-if="props.isInSidePanel">Avec affixe</template>
      <template v-else>
        <span class="md:hidden">Avec affixe</span>
        <span class="hidden md:inline">Élevage avec affixe</span>
      </template>
    </span>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { CockerCoatPalette } from '~/types/CockerCoat'
import type { LitterInfoChipsProps } from '~/types/LitterInfoChips'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { LOF_STATUS_LABELS } from '~/constants/litterLabels'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterInfoChipsProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const coatPalette: ComputedRef<CockerCoatPalette> = computed(
  (): CockerCoatPalette => COCKER_COAT_PALETTES[LitterPresentation.resolveIllustrationCoat(props.litter.colors)],
)
const chipSizeClass: ComputedRef<string> = computed((): string =>
  props.isInSidePanel
    ? 'gap-1.5 px-3 py-1.5 text-[13px] font-extrabold'
    : 'gap-1.5 px-3 py-1.5 text-[13px] font-extrabold md:gap-2 md:px-3.5 md:py-2 md:text-[15px]',
)
</script>
