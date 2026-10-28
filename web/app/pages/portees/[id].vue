<template>
  <div
    class="flex min-h-0 flex-1 flex-col lg:mx-auto lg:w-full lg:max-w-[820px]"
    :style="{ backgroundColor: tileColor }"
  >
    <div class="relative flex h-[330px] shrink-0 items-center justify-center overflow-hidden md:h-[400px]">
      <template v-if="litter">
        <img
          v-if="litter.photo_url"
          :src="litter.photo_url"
          :alt="`Photo de la portée ${litter.name}`"
          class="absolute inset-0 size-full object-cover"
          style="object-position: center 30%"
        />
        <CockerIllustration v-else :coat="coat" :size-in-pixels="200" class="mb-6" />
      </template>
      <NuxtLink
        to="/"
        aria-label="Retour aux portées"
        class="absolute top-14 left-5 inline-flex size-11 items-center justify-center rounded-full bg-card text-ink shadow-[0_2px_10px_rgba(66,43,30,0.12)] hover:text-ink md:top-9 md:left-8 md:size-[52px] md:shadow-floating"
      >
        <UiMockupIcon name="chevron-left" :size-in-pixels="22" :stroke-width="2.2" class="size-5 md:size-[22px]" />
      </NuxtLink>
      <button
        v-if="litter"
        type="button"
        :aria-label="litter.follow_up ? 'Portée suivie' : 'Ajouter au suivi'"
        :aria-pressed="litter.follow_up !== null"
        class="absolute top-14 right-5 inline-flex size-11 items-center justify-center rounded-full bg-card text-coral shadow-[0_2px_10px_rgba(66,43,30,0.12)] md:top-9 md:right-8 md:size-[52px] md:shadow-floating"
        @click="follow"
      >
        <UiMockupIcon
          :name="litter.follow_up ? 'heart-filled' : 'heart'"
          :size-in-pixels="22"
          :stroke-width="2.2"
          class="size-5 md:size-[22px]"
        />
      </button>
      <span
        v-if="badge"
        class="absolute top-11 left-1/2 hidden -translate-x-1/2 rounded-full bg-card px-4 py-1.5 text-sm leading-normal font-extrabold tracking-[0.02em] whitespace-nowrap text-coral-text md:inline"
      >
        {{ badge }}
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
            <span v-if="badge" class="text-xs font-extrabold tracking-[0.04em] text-coral-text md:hidden">{{
              badge
            }}</span>
            <h1 class="m-0 font-display text-[26px] leading-[1.1] font-semibold md:text-[34px]">{{ litter.name }}</h1>
            <span class="inline-flex items-center gap-1.5 text-sm text-ink-muted md:text-[17px]">
              <UiMockupIcon name="pin" :size-in-pixels="18" :stroke-width="2" class="hidden md:block" />
              {{ LitterDetailPresentation.placeLine(litter) }}
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
            <span class="text-[15px] font-bold md:text-[17px]">{{ LitterDetailPresentation.sourceLine(listing) }}</span>
          </span>
          <UiMockupIcon
            name="external-link"
            :size-in-pixels="20"
            :stroke-width="2.2"
            class="shrink-0 text-coral-text"
          />
        </a>
      </div>

      <div
        class="flex shrink-0 gap-2.5 border-t border-line bg-cream px-5 pt-3 pb-[26px] md:gap-3 md:px-8 md:pt-4 md:pb-[30px]"
      >
        <a
          v-if="primaryAction"
          :href="primaryAction.href"
          :target="primaryAction.isCall ? undefined : '_blank'"
          :rel="primaryAction.isCall ? undefined : 'noopener'"
          class="inline-flex min-h-[54px] grow items-center justify-center gap-2 rounded-full bg-coral px-4 text-[17px] font-extrabold text-white no-underline hover:text-white md:min-h-[60px] md:gap-2.5 md:text-[19px]"
        >
          <UiMockupIcon
            :name="primaryAction.isCall ? 'phone' : 'external-link'"
            :size-in-pixels="20"
            :stroke-width="2.2"
            class="size-[18px] md:size-5"
          />
          {{ primaryAction.label }}
        </a>
        <button
          type="button"
          :aria-pressed="litter.follow_up !== null"
          :aria-label="litter.follow_up ? 'Portée suivie' : 'Suivre cette portée'"
          class="inline-flex size-[58px] shrink-0 items-center justify-center rounded-full border-2 border-ink bg-card text-ink md:size-auto md:min-h-16 md:px-[28px] md:text-[19px] md:font-extrabold"
          @click="follow"
        >
          <UiMockupIcon
            :name="litter.follow_up ? 'heart-filled' : 'heart'"
            :size-in-pixels="22"
            :stroke-width="2.2"
            class="md:hidden"
          />
          <span class="hidden md:inline">{{ litter.follow_up ? 'Suivie' : 'Suivre' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { CockerCoat } from '~/constants/cockerCoatPalettes'
import type { LitterDetail } from '~/types/api'
import type { LitterPrimaryAction } from '~/utils/litterDetailPresentation'
import { computed, onMounted, ref } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { LittersService } from '~/services/littersService'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Photos shown in the gallery before the « + N » tile. */
const GALLERY_VISIBLE_PHOTO_COUNT: number = 3

definePageMeta({ isPushedScreen: true })

const route: RouteLocationNormalizedLoaded = useRoute()
const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const litter: Ref<LitterDetail | null> = ref(null)
const loadError: Ref<string | null> = ref(null)

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat =>
  litter.value ? LitterPresentation.coatOf(litter.value.colors) : 'inconnue',
)
const tileColor: ComputedRef<string> = computed((): string => COCKER_COAT_PALETTES[coat.value].tile)
const badge: ComputedRef<string | null> = computed((): string | null =>
  litter.value ? LitterDetailPresentation.badge(litter.value, new Date()) : null,
)
const primaryAction: ComputedRef<LitterPrimaryAction | null> = computed((): LitterPrimaryAction | null =>
  litter.value ? LitterDetailPresentation.primaryAction(litter.value) : null,
)
// The first photo heads the screen; the gallery shows the others.
const otherPhotos: ComputedRef<string[]> = computed((): string[] => (litter.value?.photos ?? []).slice(1))
const galleryPhotos: ComputedRef<string[]> = computed((): string[] =>
  otherPhotos.value.slice(0, GALLERY_VISIBLE_PHOTO_COUNT),
)
const hiddenPhotoCount: ComputedRef<number> = computed((): number =>
  Math.max(0, otherPhotos.value.length - GALLERY_VISIBLE_PHOTO_COUNT),
)

useHead({ title: (): string => `${litter.value?.name ?? 'Portée'} · La Bonne Truffe` })

/**
 * Follow the litter (« Suivre »), which starts its follow-up at « à appeler ».
 */
async function follow(): Promise<void> {
  if (litter.value !== null) {
    litter.value = await littersStore.follow(litter.value)
  }
}

onMounted(async (): Promise<void> => {
  try {
    litter.value = await LittersService.get(Number(route.params['id']))
  } catch (error: unknown) {
    loadError.value = error instanceof Error ? error.message : 'Portée introuvable'
  }
})
</script>
