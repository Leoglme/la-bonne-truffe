<template>
  <img
    v-if="props.breeder.photo_url"
    :src="props.breeder.photo_url"
    alt=""
    decoding="async"
    class="size-full object-cover"
    style="object-position: center 40%"
  />
  <span v-else class="flex size-full items-end justify-center overflow-hidden bg-gold-pastel">
    <CockerIllustration coat="gold" :size-in-pixels="props.illustrationSizeInPixels" class="-mb-4" />
  </span>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { BreederCard } from '~/types/api'
import type { BreederCoverProps } from '~/types/BreederCover'

const props: BreederCoverProps = defineProps({
  breeder: { type: Object as PropType<BreederCard>, required: true },
  illustrationSizeInPixels: { type: Number, default: 160 },
})
</script>
