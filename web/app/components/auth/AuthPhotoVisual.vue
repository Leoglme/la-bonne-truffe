<template>
  <div
    class="relative flex flex-col items-center xl:h-full xl:justify-center xl:overflow-hidden xl:rounded-4xl xl:bg-linear-to-br xl:from-gold-pastel xl:via-cream xl:to-coral-pastel xl:px-10"
  >
    <div class="flex w-full items-center justify-center">
      <div
        v-if="props.leftPhotoPath"
        class="hidden aspect-[2/3] w-1/3 max-w-xs shrink-0 translate-y-8 -rotate-6 overflow-hidden rounded-card shadow-straddling-photo ring-8 ring-card xl:-me-[8%] xl:block"
      >
        <img :src="props.leftPhotoPath" alt="" loading="lazy" class="block size-full object-cover" />
      </div>
      <div
        class="relative z-10 w-full overflow-hidden rounded-card-compact bg-gold-pastel md:rounded-card xl:aspect-[2/3] xl:h-auto xl:max-h-[68dvh] xl:w-5/12 xl:max-w-md xl:shrink-0 xl:shadow-straddling-photo xl:ring-8 xl:ring-card"
        :class="props.heightClass"
      >
        <img
          :src="props.photoPath"
          :alt="props.photoDescription"
          class="block size-full object-cover"
          :class="props.photoPositionClass"
        />
        <AuthVisualBadge v-if="props.badgeIconName" :icon-name="props.badgeIconName" />
      </div>
      <div
        v-if="props.rightPhotoPath"
        class="hidden aspect-[2/3] w-1/3 max-w-xs shrink-0 translate-y-8 rotate-6 overflow-hidden rounded-card shadow-straddling-photo ring-8 ring-card xl:-ms-[8%] xl:block"
      >
        <img :src="props.rightPhotoPath" alt="" loading="lazy" class="block size-full object-cover" />
      </div>
    </div>
    <div v-if="slots['overlay']" class="relative z-20 max-w-full xl:max-w-none" :class="props.overlayOverlapClass">
      <slot name="overlay" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Slots } from 'vue'
import type { AuthPhotoVisualProps } from '~/types/AuthPhotoVisual'
import { useSlots } from 'vue'

const props: AuthPhotoVisualProps = defineProps({
  photoPath: { type: String, required: true },
  photoDescription: { type: String, required: true },
  heightClass: { type: String, required: true },
  photoPositionClass: { type: String, default: 'object-center' },
  badgeIconName: { type: String, default: '' },
  overlayOverlapClass: { type: String, default: '-mt-[30px] md:-mt-11' },
  leftPhotoPath: { type: String, default: '' },
  rightPhotoPath: { type: String, default: '' },
})

const slots: Slots = useSlots()
</script>
