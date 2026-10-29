<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
    <div
      class="flex min-h-0 flex-1 touch-pan-y touch-pinch-zoom flex-col lg:mx-auto lg:w-full lg:max-w-[820px]"
      :class="tileClass"
      :style="swipeStyle"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchCancel"
    >
      <div class="relative flex h-[330px] shrink-0 items-center justify-center overflow-hidden md:h-[400px]">
        <button
          v-if="litter && litter.photos.length > 0"
          type="button"
          :aria-label="
            litter.photos.length > 1 ? `Voir les ${litter.photos.length} photos en grand` : 'Voir la photo en grand'
          "
          class="absolute inset-0 border-0 bg-transparent p-0"
          @click="openPhotoViewer(0)"
        >
          <LitterVisual :litter="litter" photo-position="center 30%" />
        </button>
        <LitterVisual
          v-else-if="litter"
          :litter="litter"
          :illustration-size-in-pixels="200"
          illustration-class="mb-6"
        />
        <NuxtLink
          to="/"
          aria-label="Retour aux portées"
          class="absolute top-4 left-5 inline-flex size-11 items-center justify-center rounded-full bg-card text-ink shadow-floating-over-photo hover:text-ink md:top-9 md:left-8 md:size-[52px] md:shadow-floating"
        >
          <UIcon name="i-lucide-chevron-left" class="size-5 md:size-[22px]" />
        </NuxtLink>
        <button
          v-if="litter"
          type="button"
          :aria-label="litter.follow_up ? 'Suivie, gérer le suivi' : 'Ajouter au suivi'"
          :aria-haspopup="litter.follow_up ? 'dialog' : undefined"
          :aria-busy="isFollowUpActionRunning"
          :disabled="isFollowUpActionRunning"
          class="absolute top-4 right-5 inline-flex size-11 items-center justify-center rounded-full bg-card text-coral shadow-floating-over-photo md:top-9 md:right-8 md:size-[52px] md:shadow-floating"
          @click="followOrOpenFollowUp"
        >
          <UIcon
            v-if="isFollowUpActionRunning"
            name="i-lucide-loader-circle"
            class="size-5 animate-spin md:size-[22px]"
          />
          <UiCustomIcon
            v-else
            :name="litter.follow_up ? 'heart-filled' : 'heart'"
            :size-in-pixels="22"
            :stroke-width="2.2"
            class="size-5 md:size-[22px]"
          />
        </button>
        <span
          v-if="photoBadge"
          class="absolute top-11 left-1/2 hidden -translate-x-1/2 rounded-full bg-card px-4 py-1.5 text-sm leading-normal font-extrabold tracking-[0.02em] whitespace-nowrap text-coral-text md:inline"
        >
          {{ photoBadge }}
        </span>
        <span
          v-if="litter && litter.photos.length > 1"
          aria-hidden="true"
          class="pointer-events-none absolute right-5 bottom-11 inline-flex items-center gap-1.5 rounded-full bg-ink/70 px-3 py-1.5 text-[13px] font-extrabold text-cream md:right-8 md:bottom-6 md:text-sm"
        >
          <UIcon name="i-lucide-images" class="size-4" />
          {{ litter.photos.length }} photos
        </span>
      </div>

      <p v-if="loadError" role="alert" class="m-0 p-8 text-[15px] font-bold text-coral-text">{{ loadError }}</p>
      <div
        v-else-if="litter"
        class="relative -mt-7 flex min-h-0 flex-1 flex-col overflow-hidden rounded-t-[28px] bg-cream md:mt-0 md:rounded-t-[36px]"
      >
        <div
          ref="contentScroller"
          class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-5 pt-[22px] pb-4 md:gap-6 md:px-8 md:pt-8 md:pb-6"
        >
          <div class="flex shrink-0 items-start justify-between gap-3 md:gap-4">
            <div class="flex min-w-0 flex-col gap-0.5 md:gap-1">
              <span v-if="photoBadge" class="text-xs font-extrabold tracking-[0.04em] text-coral-text md:hidden">{{
                photoBadge
              }}</span>
              <h1 class="m-0 font-display text-[26px] leading-[1.1] font-semibold md:text-[34px]">{{ litter.name }}</h1>
              <span class="inline-flex items-center gap-1.5 text-sm text-ink-muted md:text-[17px]">
                <UiCustomIcon name="pin" :size-in-pixels="18" :stroke-width="2" class="hidden md:block" />
                {{ LitterDetailPresentation.buildTownAndDepartment(litter) }}
              </span>
            </div>
            <LitterScoreBubble :litter="litter" />
          </div>
          <LitterKeyFacts :litter="litter" class="shrink-0" />
          <LitterInfoChips :litter="litter" class="shrink-0" />
          <div v-if="litter.photos.length > 1" class="grid shrink-0 grid-cols-4 gap-2 md:flex md:gap-2.5">
            <button
              v-for="(photo, photoIndex) in galleryPhotos"
              :key="photo"
              type="button"
              :aria-label="`Voir la photo ${photoIndex + 2} en grand`"
              class="aspect-square overflow-hidden rounded-2xl border-0 bg-chip p-0 md:size-[118px] md:rounded-[20px]"
              @click="openPhotoViewer(photoIndex + 1)"
            >
              <img :src="photo" alt="" class="size-full object-cover" />
            </button>
            <button
              v-if="hiddenPhotoCount > 0"
              type="button"
              :aria-label="`Voir les ${hiddenPhotoCount} autres photos`"
              class="inline-flex aspect-square items-center justify-center rounded-2xl border-0 bg-chip text-base font-extrabold text-ink-secondary md:size-[118px] md:rounded-[20px]"
              @click="openPhotoViewer(GALLERY_VISIBLE_PHOTO_COUNT + 1)"
            >
              + {{ hiddenPhotoCount }}
            </button>
          </div>
          <LitterReasonsCard :litter="litter" class="shrink-0" />
          <LitterParentsList :litter="litter" class="shrink-0" />
          <LitterListingsList :litter="litter" class="shrink-0" />
        </div>

        <div
          v-if="primaryAction"
          class="flex shrink-0 border-t border-line bg-cream px-5 pt-3 pb-[26px] md:px-8 md:pt-4 md:pb-[30px]"
        >
          <UButton
            :to="primaryAction.href"
            :target="primaryAction.isCall ? undefined : '_blank'"
            size="xl"
            class="min-h-[54px] w-full justify-center gap-2 px-4 text-[17px] md:min-h-[60px] md:gap-2.5 md:text-[19px]"
          >
            <template #leading>
              <UiCustomIcon
                v-if="primaryAction.isCall"
                name="phone"
                :size-in-pixels="20"
                :stroke-width="2.2"
                class="size-[18px] md:size-5"
              />
              <UIcon v-else name="i-lucide-external-link" class="size-[18px] md:size-5" />
            </template>
            {{ primaryAction.label }}
          </UButton>
        </div>
      </div>
    </div>

    <UiPhotoViewer
      v-if="litter"
      v-model:open="isPhotoViewerOpen"
      :photos="viewerPhotos"
      :start-index="photoViewerStartIndex"
    />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router'
import type { LitterDetail } from '~/types/api'
import type { HorizontalSwipeDirection, UseHorizontalSwipeReturn } from '~/types/Composables'
import type { LitterBrowsingOrigin, LitterPrimaryAction } from '~/types/Litter'
import type { UiPhotoViewerPhoto } from '~/types/UiPhotoViewer'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

definePageMeta({ isPushedScreen: true, key: 'litter-detail' })

const route: RouteLocationNormalizedLoaded = useRoute()
const router: Router = useRouter()
const toast: ReturnType<typeof useToast> = useToast()
const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
const { swipeStyle, onTouchStart, onTouchMove, onTouchEnd, onTouchCancel }: UseHorizontalSwipeReturn =
  useHorizontalSwipe({ canSwipeTo, showNeighbor })

const GALLERY_VISIBLE_PHOTO_COUNT: number = 3
const FOLLOW_UPS_PATH: string = '/suivi'

const contentScroller: Ref<HTMLElement | null> = ref(null)
const loadError: Ref<string | null> = ref(null)
const isFollowUpActionRunning: Ref<boolean> = ref(false)
const browsableLitterIds: Ref<number[]> = ref([])
const isPhotoViewerOpen: Ref<boolean> = ref(false)
const photoViewerStartIndex: Ref<number> = ref(0)

const litterId: ComputedRef<number> = computed((): number => Number(route.params['id']))
const litter: ComputedRef<LitterDetail | null> = computed((): LitterDetail | null =>
  littersStore.selectedLitter?.id === litterId.value ? littersStore.selectedLitter : null,
)
const tileClass: ComputedRef<string> = computed((): string =>
  LitterPresentation.resolveTileClass(litter.value?.colors ?? []),
)
const photoBadge: ComputedRef<string | null> = computed((): string | null =>
  litter.value ? LitterDetailPresentation.buildPhotoBadge(litter.value, new Date()) : null,
)
const primaryAction: ComputedRef<LitterPrimaryAction | null> = computed((): LitterPrimaryAction | null =>
  litter.value ? LitterDetailPresentation.resolvePrimaryAction(litter.value) : null,
)
const otherPhotos: ComputedRef<string[]> = computed((): string[] => (litter.value?.photos ?? []).slice(1))
const galleryPhotos: ComputedRef<string[]> = computed((): string[] =>
  otherPhotos.value.slice(0, GALLERY_VISIBLE_PHOTO_COUNT),
)
const hiddenPhotoCount: ComputedRef<number> = computed((): number =>
  Math.max(0, otherPhotos.value.length - GALLERY_VISIBLE_PHOTO_COUNT),
)
const viewerPhotos: ComputedRef<UiPhotoViewerPhoto[]> = computed((): UiPhotoViewerPhoto[] =>
  litter.value ? LitterDetailPresentation.buildViewerPhotos(litter.value) : [],
)
const pageTitle: ComputedRef<string> = computed((): string => `${litter.value?.name ?? 'Portée'} · La Bonne Truffe`)

/**
 * Load a litter into the screen, and say why when it cannot be read.
 *
 * @param id - The litter.
 */
async function loadLitter(id: number): Promise<void> {
  loadError.value = null
  try {
    await littersStore.select(id)
  } catch (error: unknown) {
    loadError.value = error instanceof Error ? error.message : 'Portée introuvable'
  }
}

/**
 * Find the litter beside this one, in the order of the screen it was opened from.
 *
 * @param direction - The side to look at.
 * @returns The id of the neighbour, or null at an end of the list.
 */
function findNeighborId(direction: HorizontalSwipeDirection): number | null {
  const position: number = browsableLitterIds.value.indexOf(litterId.value)
  if (position === -1) {
    return null
  }
  return browsableLitterIds.value[direction === 'next' ? position + 1 : position - 1] ?? null
}

/**
 * Whether a swipe has a litter to show on that side.
 *
 * @param direction - The side of the swipe.
 * @returns True when a neighbour exists.
 */
function canSwipeTo(direction: HorizontalSwipeDirection): boolean {
  return findNeighborId(direction) !== null
}

/**
 * Show the neighbouring litter in place of this one, without adding a step to the back history.
 *
 * @param direction - The side of the swipe.
 */
async function showNeighbor(direction: HorizontalSwipeDirection): Promise<void> {
  const neighborId: number | null = findNeighborId(direction)
  if (neighborId === null) {
    return
  }
  await loadLitter(neighborId)
  await router.replace(`/portees/${neighborId}`)
  await nextTick()
  contentScroller.value?.scrollTo({ top: 0 })
}

/**
 * Follow the litter, or open its follow-up drawer once it is followed.
 */
async function followOrOpenFollowUp(): Promise<void> {
  if (litter.value === null) {
    return
  }
  isFollowUpActionRunning.value = true
  try {
    await littersStore.followOrOpenFollowUp(litter.value)
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Suivi impossible', color: 'error' })
  } finally {
    isFollowUpActionRunning.value = false
  }
}

/**
 * Open the full-screen photos on one of them.
 *
 * @param photoIndex - The photo to start from.
 */
function openPhotoViewer(photoIndex: number): void {
  photoViewerStartIndex.value = photoIndex
  isPhotoViewerOpen.value = true
}

/**
 * Tell from the back history whether the detail was opened from the follow-up screen.
 *
 * @returns Where the swipe takes its order of litters from.
 */
function resolveBrowsingOrigin(): LitterBrowsingOrigin {
  const previousPath: unknown = router.options.history.state['back']
  return typeof previousPath === 'string' && previousPath.startsWith(FOLLOW_UPS_PATH) ? 'follow-ups' : 'home'
}

useHead({ title: pageTitle })

watch(litterId, async (id: number): Promise<void> => {
  if (littersStore.selectedLitter?.id !== id) {
    await loadLitter(id)
  }
})

onMounted(async (): Promise<void> => {
  await loadLitter(litterId.value)
  browsableLitterIds.value = await littersStore.listBrowsableLitterIds(resolveBrowsingOrigin(), litterId.value)
})
</script>
