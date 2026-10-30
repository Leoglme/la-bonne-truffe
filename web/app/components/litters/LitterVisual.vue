<template>
  <img
    v-if="props.litter.photo_url && !hasPhotoFailed"
    :src="props.litter.photo_url"
    :alt="`Photo de la portée ${props.litter.name}`"
    loading="lazy"
    decoding="async"
    class="absolute inset-0 size-full rounded-[inherit] object-cover"
    :style="{ objectPosition: props.photoPosition }"
    @error="hasPhotoFailed = true"
  />
  <CockerIllustration
    v-else
    :coat="coat"
    :size-in-pixels="props.illustrationSizeInPixels"
    :class="props.illustrationClass"
  />
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { LitterCard } from '~/types/api'
import type { CockerCoat } from '~/types/CockerCoat'
import type { LitterVisualProps } from '~/types/LitterVisual'
import { computed, ref, watch } from 'vue'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterVisualProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
  illustrationSizeInPixels: { type: Number, default: 132 },
  photoPosition: { type: String, default: 'center' },
  illustrationClass: { type: String, default: '' },
})

const hasPhotoFailed: Ref<boolean> = ref(false)

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat =>
  LitterPresentation.resolveIllustrationCoat(props.litter.colors),
)

watch(
  (): string | null => props.litter.photo_url,
  (): void => {
    hasPhotoFailed.value = false
  },
)
</script>
