<template>
  <div class="flex flex-wrap" :class="props.variant === 'panel' ? 'gap-2' : 'gap-2 md:gap-2.5'">
    <span
      class="inline-flex items-center rounded-full font-extrabold"
      :class="chipSizeClass"
      :style="{ backgroundColor: colorChipBackground, color: colorChipText }"
    >
      <span
        class="shrink-0 rounded-full"
        :class="props.variant === 'panel' ? 'size-2.5' : 'size-2.5 md:size-3'"
        :style="{ backgroundColor: coatPalette.coat }"
        aria-hidden="true"
      />
      {{ LitterPresentation.colorLabel(props.litter.colors, true) }}
    </span>
    <span
      v-if="props.litter.lof_status === 'lof'"
      class="rounded-full bg-lof-pastel text-lof-ink"
      :class="chipSizeClass"
    >
      LOF
    </span>
    <span v-else class="rounded-full bg-chip text-ink-secondary" :class="chipSizeClass">
      {{ props.litter.lof_status === 'non_lof' ? 'Non LOF' : 'LOF à confirmer' }}
    </span>
    <span v-if="props.litter.breeder?.has_affix" class="rounded-full bg-chip text-ink-secondary" :class="chipSizeClass">
      <template v-if="props.variant === 'panel'">Avec affixe</template>
      <template v-else>
        <span class="md:hidden">Avec affixe</span>
        <span class="hidden md:inline">Élevage avec affixe</span>
      </template>
    </span>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { CockerCoat, CockerCoatPalette } from '~/constants/cockerCoatPalettes'
import type { LitterDetail } from '~/types/api'
import type { LitterDetailVariant } from '~/types/LitterDetailVariant'
import type { LitterInfoChipsProps } from '~/types/LitterInfoChips'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Colour, LOF and affix chips of a litter (the gold chip of the mockup, the green LOF chip). */
const props: LitterInfoChipsProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  variant: { type: String as PropType<LitterDetailVariant>, default: 'responsive' },
})

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat => LitterPresentation.coatOf(props.litter.colors))
const coatPalette: ComputedRef<CockerCoatPalette> = computed((): CockerCoatPalette => COCKER_COAT_PALETTES[coat.value])
const colorChipBackground: ComputedRef<string> = computed((): string =>
  coat.value === 'gold' ? '#FBE7CC' : coatPalette.value.tile,
)
const colorChipText: ComputedRef<string> = computed((): string => (coat.value === 'gold' ? '#8A5A14' : '#5E4B3F'))
const chipSizeClass: ComputedRef<string> = computed((): string =>
  props.variant === 'panel'
    ? 'gap-1.5 px-3 py-1.5 text-[13px] font-extrabold'
    : 'gap-1.5 px-3 py-1.5 text-[13px] font-extrabold md:gap-2 md:px-3.5 md:py-2 md:text-[15px]',
)
</script>
