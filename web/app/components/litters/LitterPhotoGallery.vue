<template>
  <div class="flex flex-col gap-3">
    <LitterTileFrame
      v-if="shownPhoto === null"
      :litter="props.litter"
      class="aspect-[4/3] w-full overflow-hidden rounded-card-compact md:rounded-card"
    >
      <LitterVisual :litter="props.litter" :illustration-size-in-pixels="180" />
    </LitterTileFrame>
    <div
      v-else
      class="relative aspect-[4/5] w-full overflow-hidden rounded-card-compact md:aspect-[4/3] md:rounded-card"
      :class="tileClass"
    >
      <img
        :src="shownPhoto"
        alt=""
        aria-hidden="true"
        class="absolute inset-0 size-full scale-110 object-cover opacity-50 blur-2xl"
      />
      <button
        type="button"
        :aria-label="`Voir la photo ${shownPhotoIndex + 1} sur ${props.litter.photos.length} en grand`"
        class="absolute inset-0 border-0 bg-transparent p-0"
        @click="isPhotoViewerOpen = true"
      >
        <img
          :src="shownPhoto"
          :alt="`Photo ${shownPhotoIndex + 1} de la portée ${props.litter.name}`"
          decoding="async"
          class="size-full object-contain"
        />
      </button>
      <template v-if="props.litter.photos.length > 1">
        <button
          type="button"
          aria-label="Photo précédente"
          class="absolute top-1/2 left-3 inline-flex size-11 -translate-y-1/2 items-center justify-center rounded-full border-0 bg-card text-ink shadow-floating-over-photo"
          @click="showPhoto(shownPhotoIndex - 1)"
        >
          <UIcon name="i-lucide-chevron-left" class="size-5" />
        </button>
        <button
          type="button"
          aria-label="Photo suivante"
          class="absolute top-1/2 right-3 inline-flex size-11 -translate-y-1/2 items-center justify-center rounded-full border-0 bg-card text-ink shadow-floating-over-photo"
          @click="showPhoto(shownPhotoIndex + 1)"
        >
          <UIcon name="i-lucide-chevron-right" class="size-5" />
        </button>
        <span
          aria-hidden="true"
          class="pointer-events-none absolute right-3 bottom-3 rounded-full bg-ink/70 px-3 py-1.5 text-[13px] font-extrabold text-cream"
        >
          {{ shownPhotoIndex + 1 }} / {{ props.litter.photos.length }}
        </span>
      </template>
    </div>

    <div v-if="props.litter.photos.length > 1" class="scrollbar-hidden flex gap-2 overflow-x-auto">
      <button
        v-for="(photo, photoIndex) in props.litter.photos"
        :key="photo"
        type="button"
        :aria-label="`Afficher la photo ${photoIndex + 1}`"
        :aria-pressed="photoIndex === shownPhotoIndex"
        class="relative size-16 shrink-0 overflow-hidden rounded-2xl border-0 bg-chip p-0 transition-opacity md:size-[76px]"
        :class="photoIndex === shownPhotoIndex ? 'opacity-100' : 'opacity-55'"
        @click="showPhoto(photoIndex)"
      >
        <img :src="photo" alt="" loading="lazy" decoding="async" class="size-full object-cover" />
        <span
          v-if="photoIndex === shownPhotoIndex"
          aria-hidden="true"
          class="absolute inset-0 rounded-2xl border-[3px] border-coral"
        />
      </button>
    </div>

    <UiPhotoViewer v-model:open="isPhotoViewerOpen" :photos="viewerPhotos" :start-index="shownPhotoIndex" />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterPhotoGalleryProps } from '~/types/LitterPhotoGallery'
import type { UiPhotoViewerPhoto } from '~/types/UiPhotoViewer'
import { computed, ref } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterPhotoGalleryProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const shownPhotoIndex: Ref<number> = ref(0)
const isPhotoViewerOpen: Ref<boolean> = ref(false)

const shownPhoto: ComputedRef<string | null> = computed(
  (): string | null => props.litter.photos[shownPhotoIndex.value] ?? null,
)
const tileClass: ComputedRef<string> = computed((): string => LitterPresentation.resolveTileClass(props.litter.colors))
const viewerPhotos: ComputedRef<UiPhotoViewerPhoto[]> = computed((): UiPhotoViewerPhoto[] =>
  LitterDetailPresentation.buildViewerPhotos(props.litter),
)

/**
 * Show another photo in the large frame, the first after the last and the last before the first.
 *
 * @param photoIndex - The photo wanted, possibly one step outside the list.
 */
function showPhoto(photoIndex: number): void {
  const photoCount: number = props.litter.photos.length
  shownPhotoIndex.value = (photoIndex + photoCount) % photoCount
}
</script>
