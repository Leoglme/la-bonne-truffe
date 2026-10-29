<template>
  <UModal
    :open="props.open"
    fullscreen
    :title="`Photo ${currentIndex + 1} sur ${props.photos.length}`"
    description="Glisse pour passer d’une photo à l’autre."
    :ui="{ content: 'divide-y-0 bg-ink' }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #content="{ close }">
      <div class="flex h-full flex-col text-cream">
        <div class="flex shrink-0 items-center justify-between gap-3 px-5 pt-4 pb-2 md:px-8 md:pt-6">
          <span aria-hidden="true" class="text-[15px] font-extrabold md:text-[17px]">
            {{ currentIndex + 1 }} / {{ props.photos.length }}
          </span>
          <button
            type="button"
            aria-label="Fermer les photos"
            class="inline-flex size-11 items-center justify-center rounded-full border-0 bg-cream/15 text-cream md:size-[52px]"
            @click="close"
          >
            <UIcon name="i-lucide-x" class="size-6" />
          </button>
        </div>
        <UCarousel
          v-slot="{ item }"
          :items="props.photos"
          :start-index="props.startIndex"
          :arrows="props.photos.length > 1"
          class="min-h-0 flex-1"
          :ui="{
            viewport: 'h-full',
            container: 'ms-0 h-full',
            item: 'flex h-full items-center justify-center ps-0',
            prev: 'start-6 hidden size-12 justify-center p-0 sm:start-6 md:inline-flex',
            next: 'end-6 hidden size-12 justify-center p-0 sm:end-6 md:inline-flex',
          }"
          @select="showCaptionOf"
        >
          <img
            :src="item.url"
            :alt="item.caption ?? 'Photo de la portée'"
            draggable="false"
            class="max-h-full max-w-full object-contain select-none"
          />
        </UCarousel>
        <p class="m-0 flex min-h-20 shrink-0 justify-center px-5 pt-4 text-center text-[17px] font-bold md:text-[19px]">
          {{ currentCaption }}
        </p>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { UiPhotoViewerEmits, UiPhotoViewerPhoto, UiPhotoViewerProps } from '~/types/UiPhotoViewer'
import { computed, ref, watch } from 'vue'

const props: UiPhotoViewerProps = defineProps({
  open: { type: Boolean, required: true },
  photos: { type: Array as PropType<UiPhotoViewerPhoto[]>, required: true },
  startIndex: { type: Number, default: 0 },
})

const emit: UiPhotoViewerEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const currentIndex: Ref<number> = ref(props.startIndex)

const currentCaption: ComputedRef<string> = computed((): string => props.photos[currentIndex.value]?.caption ?? '')

/**
 * Follow the photo shown, for the counter and the caption.
 *
 * @param photoIndex - Index of the photo the carousel settled on.
 */
function showCaptionOf(photoIndex: number): void {
  currentIndex.value = photoIndex
}

watch(
  (): boolean => props.open,
  (isOpen: boolean): void => {
    if (isOpen) {
      currentIndex.value = props.startIndex
    }
  },
)
</script>
