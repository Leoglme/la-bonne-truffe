<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden font-display font-semibold"
    :class="[
      props.sizeClass,
      props.textClass,
      shownImageUrl ? 'bg-chip' : BreederPresentation.resolveTileClass(props.breeder),
    ]"
    aria-hidden="true"
  >
    <img
      v-if="shownImageUrl"
      :src="shownImageUrl"
      alt=""
      loading="lazy"
      decoding="async"
      class="size-full object-cover"
      @error="hasImageFailed = true"
    />
    <template v-else>{{ BreederPresentation.buildInitials(props.breeder.name) }}</template>
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { BreederCard } from '~/types/api'
import type { BreederAvatarTileProps } from '~/types/BreederAvatarTile'
import { computed, ref, watch } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederAvatarTileProps = defineProps({
  breeder: { type: Object as PropType<BreederCard>, required: true },
  sizeClass: { type: String, default: 'size-[72px] rounded-[20px]' },
  textClass: { type: String, default: 'text-2xl' },
})

const hasImageFailed: Ref<boolean> = ref(false)

const imageUrl: ComputedRef<string | null> = computed(
  (): string | null => props.breeder.logo_url ?? props.breeder.photo_url,
)
const shownImageUrl: ComputedRef<string | null> = computed((): string | null =>
  hasImageFailed.value ? null : imageUrl.value,
)

watch(imageUrl, (): void => {
  hasImageFailed.value = false
})
</script>
