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
    <span
      v-if="puppiesAvailableLabel"
      class="rounded-full"
      :class="[
        chipSizeClass,
        props.litter.puppies_available === 0 ? 'bg-coral-pastel text-coral-text' : 'bg-chip text-ink-secondary',
      ]"
    >
      {{ puppiesAvailableLabel }}
    </span>
    <span
      v-for="breedingQualityChip in breedingQualityChips"
      :key="breedingQualityChip"
      class="rounded-full bg-chip text-ink-secondary"
      :class="chipSizeClass"
    >
      <template v-if="props.isInSidePanel">{{ BREEDING_QUALITY_CHIP_LABELS[breedingQualityChip].shortLabel }}</template>
      <template v-else>
        <span class="md:hidden">{{ BREEDING_QUALITY_CHIP_LABELS[breedingQualityChip].shortLabel }}</span>
        <span class="hidden md:inline">{{ BREEDING_QUALITY_CHIP_LABELS[breedingQualityChip].fullLabel }}</span>
      </template>
    </span>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { CockerCoatPalette } from '~/types/CockerCoat'
import type { BreedingQualityChip, LitterInfoChipsProps } from '~/types/LitterInfoChips'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { BREEDING_QUALITY_CHIP_LABELS, LOF_STATUS_LABELS } from '~/constants/litterLabels'
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
const puppiesAvailableLabel: ComputedRef<string | null> = computed((): string | null =>
  LitterPresentation.buildPuppiesAvailableLabel(props.litter),
)
const breedingQualityChips: ComputedRef<BreedingQualityChip[]> = computed((): BreedingQualityChip[] => {
  const chips: BreedingQualityChip[] = []
  if (props.litter.breeder?.has_affix) {
    chips.push('affix')
  }
  if (props.litter.genetic_screening) {
    chips.push(props.litter.genetic_screening)
  }
  if (props.litter.breeder?.is_breed_club_member) {
    chips.push('breed_club_member')
  }
  return chips
})
</script>
