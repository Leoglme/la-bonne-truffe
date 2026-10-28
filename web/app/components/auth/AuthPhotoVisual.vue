<template>
  <div class="relative flex flex-col items-center lg:h-full">
    <div
      class="relative w-full overflow-hidden rounded-card-compact bg-gold-pastel md:rounded-card lg:h-full lg:rounded-[32px]"
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
      v-if="slots['overlay']"
      class="relative max-w-full lg:absolute lg:top-8 lg:left-8 lg:mt-0"
      :class="props.overlayOverlapClass"
    >
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
})

const slots: Slots = useSlots()
</script>
