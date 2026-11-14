<template>
  <img
    v-if="isPhotoShown"
    :src="props.litter.photo_url ?? undefined"
    :alt="`Photo de la portée ${props.litter.name}`"
    :loading="props.photoLoading"
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
  <span
    v-if="isPhotoShown && photoSourceLabel && props.photoSourceLabelClass !== null"
    class="pointer-events-none absolute z-[1] inline-flex rounded-full bg-ink/70 leading-normal font-extrabold whitespace-nowrap text-cream"
    :class="props.photoSourceLabelClass"
  >
    {{ photoSourceLabel }}
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { LitterCard } from '~/types/api'
import type { CockerCoat } from '~/types/CockerCoat'
import type { ImageLoading, LitterVisualProps } from '~/types/LitterVisual'
import { computed, ref, watch } from 'vue'
import { LITTER_PHOTO_SOURCE_LABELS } from '~/constants/litterLabels'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterVisualProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
  illustrationSizeInPixels: { type: Number, default: 132 },
  photoPosition: { type: String, default: 'center' },
  illustrationClass: { type: String, default: '' },
  photoLoading: { type: String as PropType<ImageLoading>, default: 'lazy' },
  photoSourceLabelClass: { type: String as PropType<string | null>, default: null },
})

const hasPhotoFailed: Ref<boolean> = ref(false)

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat =>
  LitterPresentation.resolveIllustrationCoat(props.litter.colors),
)
const isPhotoShown: ComputedRef<boolean> = computed(
  (): boolean => Boolean(props.litter.photo_url) && !hasPhotoFailed.value,
)
const photoSourceLabel: ComputedRef<string | null> = computed((): string | null =>
  props.litter.photo_source ? LITTER_PHOTO_SOURCE_LABELS[props.litter.photo_source] : null,
)

watch(
  (): string | null => props.litter.photo_url,
  (): void => {
    hasPhotoFailed.value = false
  },
)
</script>
