<template>
  <div class="flex min-h-0 flex-1 flex-col lg:mx-auto lg:w-full lg:max-w-[820px]" :class="tileClass">
    <div class="relative flex h-[330px] shrink-0 items-center justify-center overflow-hidden md:h-[400px]">
      <LitterVisual
        v-if="litter"
        :litter="litter"
        :illustration-size-in-pixels="200"
        photo-position="center 30%"
        illustration-class="mb-6"
      />
      <NuxtLink
        to="/"
        aria-label="Retour aux portées"
        class="absolute top-14 left-5 inline-flex size-11 items-center justify-center rounded-full bg-card text-ink shadow-floating-over-photo hover:text-ink md:top-9 md:left-8 md:size-[52px] md:shadow-floating"
      >
        <UIcon name="i-lucide-chevron-left" class="size-5 md:size-[22px]" />
      </NuxtLink>
      <button
        v-if="litter"
        type="button"
        :aria-label="litter.follow_up ? 'Portée suivie' : 'Ajouter au suivi'"
        :aria-pressed="litter.follow_up !== null"
        :aria-busy="isFollowing"
        :disabled="isFollowing"
        class="absolute top-14 right-5 inline-flex size-11 items-center justify-center rounded-full bg-card text-coral shadow-floating-over-photo md:top-9 md:right-8 md:size-[52px] md:shadow-floating"
        @click="follow"
      >
        <UIcon v-if="isFollowing" name="i-lucide-loader-circle" class="size-5 animate-spin md:size-[22px]" />
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
    </div>

    <p v-if="loadError" role="alert" class="m-0 p-8 text-[15px] font-bold text-coral-text">{{ loadError }}</p>
    <div
      v-else-if="litter"
      class="relative -mt-7 flex min-h-0 flex-1 flex-col overflow-hidden rounded-t-[28px] bg-cream md:mt-0 md:rounded-t-[36px]"
    >
      <div
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
        <div v-if="litter.photos.length > 1" class="hidden shrink-0 gap-2.5 md:flex">
          <img
            v-for="photo in galleryPhotos"
            :key="photo"
            :src="photo"
            alt="Photo de la portée"
            class="size-[118px] rounded-[20px] object-cover"
          />
          <span
            v-if="hiddenPhotoCount > 0"
            class="inline-flex size-[118px] items-center justify-center rounded-[20px] bg-chip text-base font-extrabold text-ink-secondary"
          >
            + {{ hiddenPhotoCount }}
          </span>
        </div>
        <LitterReasonsCard :litter="litter" class="shrink-0" />
        <LitterParentsList :litter="litter" class="shrink-0" />
        <a
          v-for="listing in litter.listings"
          :key="`${listing.source}-${listing.external_url}`"
          :href="listing.external_url ?? undefined"
          target="_blank"
          rel="noopener"
          class="flex min-h-14 shrink-0 items-center justify-between gap-3 rounded-2xl bg-card px-3.5 py-3 text-ink no-underline shadow-card hover:text-ink md:rounded-[20px] md:px-[18px]"
        >
          <span class="flex flex-col">
            <span class="text-[11px] font-extrabold text-ink-label md:text-[13px]">VU SUR</span>
            <span class="text-[15px] font-bold md:text-[17px]">{{
              LitterDetailPresentation.buildSourceLine(listing)
            }}</span>
          </span>
          <UIcon name="i-lucide-external-link" class="size-5 shrink-0 text-coral-text" />
        </a>
      </div>

      <div
        class="flex shrink-0 gap-2.5 border-t border-line bg-cream px-5 pt-3 pb-[26px] md:gap-3 md:px-8 md:pt-4 md:pb-[30px]"
      >
        <UButton
          v-if="primaryAction"
          :to="primaryAction.href"
          :target="primaryAction.isCall ? undefined : '_blank'"
          size="xl"
          class="min-h-[54px] grow justify-center gap-2 px-4 text-[17px] md:min-h-[60px] md:gap-2.5 md:text-[19px]"
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
        <UButton
          color="neutral"
          variant="outline"
          size="lg"
          :loading="isFollowing"
          :aria-pressed="litter.follow_up !== null"
          :aria-label="litter.follow_up ? 'Portée suivie' : 'Suivre cette portée'"
          class="size-[58px] shrink-0 justify-center px-0 md:size-auto md:min-h-16 md:px-[30px] md:text-[19px]"
          @click="follow"
        >
          <UiCustomIcon
            v-if="!isFollowing"
            :name="litter.follow_up ? 'heart-filled' : 'heart'"
            :size-in-pixels="22"
            :stroke-width="2.2"
            class="md:hidden"
          />
          <span class="hidden md:inline">{{ litter.follow_up ? 'Suivie' : 'Suivre' }}</span>
        </UButton>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { LitterDetail } from '~/types/api'
import type { LitterPrimaryAction } from '~/types/Litter'
import { computed, onMounted, ref } from 'vue'
import { LittersService } from '~/services/littersService'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

definePageMeta({ isPushedScreen: true })

const route: RouteLocationNormalizedLoaded = useRoute()
const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const GALLERY_VISIBLE_PHOTO_COUNT: number = 3

const litter: Ref<LitterDetail | null> = ref(null)
const loadError: Ref<string | null> = ref(null)
const isFollowing: Ref<boolean> = ref(false)

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
const pageTitle: ComputedRef<string> = computed((): string => `${litter.value?.name ?? 'Portée'} · La Bonne Truffe`)

/**
 * Follow the litter (« Suivre »), which starts its follow-up at « à appeler ».
 */
async function follow(): Promise<void> {
  if (litter.value === null) {
    return
  }
  isFollowing.value = true
  try {
    litter.value = await littersStore.follow(litter.value)
  } finally {
    isFollowing.value = false
  }
}

useHead({ title: pageTitle })

onMounted(async (): Promise<void> => {
  try {
    litter.value = await LittersService.get(Number(route.params['id']))
  } catch (error: unknown) {
    loadError.value = error instanceof Error ? error.message : 'Portée introuvable'
  }
})
</script>
