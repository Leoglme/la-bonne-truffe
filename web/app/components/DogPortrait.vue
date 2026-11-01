<template>
  <span
    aria-hidden="true"
    class="inline-flex shrink-0 items-center justify-center overflow-hidden"
    :class="[props.sizeClass, props.photoUrl ? 'bg-chip' : tileClass]"
  >
    <img
      v-if="props.photoUrl"
      :src="props.photoUrl"
      alt=""
      loading="lazy"
      decoding="async"
      class="size-full object-cover object-[center_30%]"
    />
    <CockerIllustration v-else :coat="coat" :size-in-pixels="props.illustrationSizeInPixels" />
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { CoatColor } from '~/types/api'
import type { CockerCoat } from '~/types/CockerCoat'
import type { DogPortraitProps } from '~/types/DogPortrait'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES, ILLUSTRATED_COATS } from '~/constants/cockerCoatPalettes'

const props: DogPortraitProps = defineProps({
  photoUrl: { type: String as PropType<string | null>, default: null },
  color: { type: String as PropType<CoatColor | null>, default: null },
  sizeClass: { type: String, required: true },
  illustrationSizeInPixels: { type: Number, required: true },
})

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat =>
  props.color === null ? 'inconnue' : (ILLUSTRATED_COATS[props.color] ?? 'inconnue'),
)
const tileClass: ComputedRef<string> = computed((): string => COCKER_COAT_PALETTES[coat.value].tileClass)
</script>
