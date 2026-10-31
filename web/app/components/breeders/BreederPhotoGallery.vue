<template>
  <section v-if="props.photos.length > 0" class="flex flex-col gap-3">
    <h2 class="m-0 font-display text-[19px] font-semibold md:text-xl">Photos de l’élevage</h2>
    <div class="grid grid-cols-4 gap-2 md:flex md:gap-2.5">
      <button
        v-for="(photo, photoIndex) in shownPhotos"
        :key="photo"
        type="button"
        :aria-label="`Voir la photo ${photoIndex + 1} en grand`"
        class="aspect-square overflow-hidden rounded-2xl border-0 bg-chip p-0 md:size-[118px] md:rounded-[20px]"
        @click="openViewer(photoIndex)"
      >
        <img :src="photo" alt="" loading="lazy" decoding="async" class="size-full object-cover" />
      </button>
      <button
        v-if="hiddenPhotoCount > 0"
        type="button"
        :aria-label="`Voir les ${hiddenPhotoCount} autres photos`"
        class="inline-flex aspect-square items-center justify-center rounded-2xl border-0 bg-chip text-base font-extrabold text-ink-secondary md:size-[118px] md:rounded-[20px]"
        @click="openViewer(SHOWN_PHOTOS_COUNT)"
      >
        + {{ hiddenPhotoCount }}
      </button>
    </div>
    <UiPhotoViewer v-model:open="isViewerOpen" :photos="viewerPhotos" :start-index="viewerStartIndex" />
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { BreederPhotoGalleryProps } from '~/types/BreederPhotoGallery'
import type { UiPhotoViewerPhoto } from '~/types/UiPhotoViewer'
import { computed, ref } from 'vue'

const SHOWN_PHOTOS_COUNT: number = 3

const props: BreederPhotoGalleryProps = defineProps({
  photos: { type: Array as PropType<string[]>, required: true },
})

const isViewerOpen: Ref<boolean> = ref(false)
const viewerStartIndex: Ref<number> = ref(0)

const shownPhotos: ComputedRef<string[]> = computed((): string[] => props.photos.slice(0, SHOWN_PHOTOS_COUNT))
const hiddenPhotoCount: ComputedRef<number> = computed((): number =>
  Math.max(0, props.photos.length - SHOWN_PHOTOS_COUNT),
)
const viewerPhotos: ComputedRef<UiPhotoViewerPhoto[]> = computed((): UiPhotoViewerPhoto[] =>
  props.photos.map((url: string): UiPhotoViewerPhoto => ({ url, caption: null })),
)

/**
 * Open the full-screen photos on one of them.
 *
 * @param photoIndex - The photo to start from.
 */
function openViewer(photoIndex: number): void {
  viewerStartIndex.value = photoIndex
  isViewerOpen.value = true
}
</script>
