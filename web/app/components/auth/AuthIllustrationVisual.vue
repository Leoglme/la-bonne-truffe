<template>
  <div
    aria-hidden="true"
    class="relative flex w-full items-center justify-center rounded-card-compact md:rounded-card lg:h-full lg:rounded-[32px]"
    :class="[palette.tileClass, props.heightClass]"
  >
    <CockerIllustration :coat="props.coat" class="size-[170px] md:size-[300px] lg:size-[340px]" />
    <AuthVisualBadge :icon-name="props.badgeIconName" />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { AuthIllustrationVisualProps } from '~/types/AuthIllustrationVisual'
import type { CockerCoat, CockerCoatPalette } from '~/types/CockerCoat'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'

const props: AuthIllustrationVisualProps = defineProps({
  coat: { type: String as PropType<CockerCoat>, required: true },
  badgeIconName: { type: String, required: true },
  heightClass: { type: String, required: true },
})

const palette: ComputedRef<CockerCoatPalette> = computed((): CockerCoatPalette => COCKER_COAT_PALETTES[props.coat])
</script>
