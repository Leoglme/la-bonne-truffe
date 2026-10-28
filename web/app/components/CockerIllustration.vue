<template>
  <svg :width="sizeInPixels" :height="sizeInPixels" viewBox="0 0 160 160" role="img" :aria-label="accessibleLabel">
    <path d="M38 62 C18 70 14 112 30 128 C44 142 58 126 56 100 Z" :fill="palette.ear" />
    <path d="M122 62 C142 70 146 112 130 128 C116 142 102 126 104 100 Z" :fill="palette.ear" />
    <circle cx="80" cy="78" r="44" :fill="palette.coat" />
    <path d="M60 42 C68 26 92 26 100 42 L80 52 Z" :fill="palette.ear" />
    <ellipse cx="80" cy="97" rx="25" ry="18" :fill="palette.muzzle" />
    <circle cx="64" cy="74" r="5.5" fill="#2B2420" />
    <circle cx="96" cy="74" r="5.5" fill="#2B2420" />
    <circle cx="66" cy="72" r="1.8" fill="#FFFFFF" />
    <circle cx="98" cy="72" r="1.8" fill="#FFFFFF" />
    <circle cx="52" cy="90" r="6" fill="#F4A7A1" opacity="0.7" />
    <circle cx="108" cy="90" r="6" fill="#F4A7A1" opacity="0.7" />
    <path d="M69 88 Q80 81 91 88 Q91 99 80 105 Q69 99 69 88 Z" fill="#2B2420" />
    <circle cx="75" cy="89" r="2" fill="#FFFFFF" opacity="0.55" />
    <path
      d="M80 105 Q80 111 73 112 M80 105 Q80 111 87 112"
      stroke="#2B2420"
      stroke-width="2.2"
      fill="none"
      stroke-linecap="round"
    />
  </svg>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { CockerCoat, CockerCoatPalette } from '~/constants/cockerCoatPalettes'
import type { CockerIllustrationProps } from '~/types/CockerIllustration'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'

/** Cocker head drawn in flat colours, painted with the coat of a litter (design/illustration-cocker.svg). */
const props: CockerIllustrationProps = defineProps({
  coat: {
    type: String as PropType<CockerCoat>,
    default: 'inconnue',
  },
  sizeInPixels: {
    type: Number,
    default: 132,
  },
})

const palette: ComputedRef<CockerCoatPalette> = computed((): CockerCoatPalette => COCKER_COAT_PALETTES[props.coat])
const accessibleLabel: ComputedRef<string> = computed((): string =>
  props.coat === 'inconnue' ? 'Chiot cocker, couleur à confirmer' : `Chiot cocker ${palette.value.label.toLowerCase()}`,
)
</script>
