<template>
  <div class="grid h-[402px] grid-cols-[2fr_1fr_1fr] grid-rows-2 gap-2.5">
    <button
      v-for="tile in tiles"
      :key="tile.photoIndex"
      type="button"
      :aria-label="tile.ariaLabel"
      class="relative overflow-hidden border-0 bg-chip p-0"
      :class="tile.placementClass"
      @click="emit('open', tile.photoIndex)"
    >
      <img
        :src="tile.photo"
        alt=""
        :loading="tile.photoIndex === 0 ? 'eager' : 'lazy'"
        decoding="async"
        class="size-full object-cover"
        :style="tile.photoIndex === 0 ? { objectPosition: props.firstPhotoPosition } : undefined"
      />
      <span
        v-if="tile.photoIndex === 0 && props.badgeLabel"
        class="absolute top-4 left-4 rounded-full bg-card px-3.5 py-[5px] text-[13px] leading-normal font-extrabold tracking-[0.02em] text-coral-text uppercase"
      >
        {{ props.badgeLabel }}
      </span>
      <span
        v-if="tile.photoIndex === lastTileIndex && props.photos.length > 1"
        aria-hidden="true"
        class="pointer-events-none absolute right-3 bottom-3 inline-flex items-center gap-1.5 rounded-full bg-ink/70 px-3 py-1.5 text-sm font-extrabold text-cream"
      >
        <UIcon name="i-lucide-images" class="size-4" />
        {{ props.photos.length }} photos
      </span>
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { UiPhotoMosaicEmits, UiPhotoMosaicProps, UiPhotoMosaicTile } from '~/types/UiPhotoMosaic'
import { computed } from 'vue'
import { PHOTO_MOSAIC_MAXIMUM_TILE_COUNT, PHOTO_MOSAIC_TILE_CLASSES_BY_COUNT } from '~/constants/photoMosaic'

const props: UiPhotoMosaicProps = defineProps({
  photos: { type: Array as PropType<string[]>, required: true },
  badgeLabel: { type: String as PropType<string | null>, default: null },
  firstPhotoPosition: { type: String, default: 'center' },
})

const emit: UiPhotoMosaicEmits = defineEmits<{
  (event: 'open', photoIndex: number): void
}>()

const tiles: ComputedRef<UiPhotoMosaicTile[]> = computed((): UiPhotoMosaicTile[] => {
  const shownPhotos: string[] = props.photos.slice(0, PHOTO_MOSAIC_MAXIMUM_TILE_COUNT)
  const placementClasses: string[] = PHOTO_MOSAIC_TILE_CLASSES_BY_COUNT[shownPhotos.length] ?? []
  return shownPhotos.map((photo: string, photoIndex: number): UiPhotoMosaicTile => ({
    photo,
    photoIndex,
    ariaLabel: buildTileAriaLabel(photoIndex),
    placementClass: placementClasses[photoIndex] ?? '',
  }))
})
const lastTileIndex: ComputedRef<number> = computed((): number => tiles.value.length - 1)

/**
 * Say what a tile opens.
 *
 * @param photoIndex - The photo of the tile.
 * @returns The accessible name of the tile.
 */
function buildTileAriaLabel(photoIndex: number): string {
  if (photoIndex > 0) {
    return `Voir la photo ${photoIndex + 1} en grand`
  }
  return props.photos.length > 1 ? `Voir les ${props.photos.length} photos en grand` : 'Voir la photo en grand'
}
</script>
