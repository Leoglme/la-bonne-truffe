<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-6 px-5 pt-8 pb-12 md:gap-7 md:px-8 md:pt-12">
    <span class="inline-flex items-center gap-2 text-ink-muted">
      <UiAppIcon class="size-7" />
      <span class="font-display text-[17px] font-semibold">La Bonne Truffe</span>
    </span>

    <template v-if="sharedLitter">
      <div class="flex flex-col gap-3">
        <h1 class="m-0 font-display text-[26px] leading-[1.15] font-semibold md:text-[32px]">
          {{ LitterSharePresentation.buildTitle(sharedLitter.sharer_name) }}
        </h1>
        <div v-if="sharedLitter.message" class="flex items-start gap-3">
          <span
            aria-hidden="true"
            class="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-avatar font-display text-base font-semibold"
          >
            {{ sharerInitial }}
          </span>
          <p
            class="m-0 rounded-[4px_18px_18px_18px] bg-card px-3.5 py-2.5 text-[15px] whitespace-pre-line shadow-card md:text-[17px]"
          >
            {{ sharedLitter.message }}
          </p>
        </div>
      </div>

      <LitterPhotoGallery :litter="sharedLitter.litter" />

      <div class="flex flex-col gap-1">
        <span v-if="birthLabel" class="text-xs font-extrabold tracking-[0.04em] text-coral-text md:text-sm">{{
          birthLabel
        }}</span>
        <h2 class="m-0 font-display text-[28px] leading-[1.1] font-semibold md:text-[34px]">
          {{ sharedLitter.litter.name }}
        </h2>
        <span class="text-[15px] text-ink-muted md:text-[17px]">
          {{ LitterDetailPresentation.buildTownAndDepartment(sharedLitter.litter, null) }}
        </span>
      </div>

      <LitterKeyFacts :litter="sharedLitter.litter" />
      <LitterInfoChips :litter="sharedLitter.litter" />
      <LitterParentsList :litter="sharedLitter.litter" is-title-shown-on-phone />
      <LitterBreederCard :litter="sharedLitter.litter" is-phone-shown />
      <LitterListingsList :litter="sharedLitter.litter" />

      <p class="m-0 text-center text-[13px] text-ink-muted">
        {{ LitterSharePresentation.buildExpiryLine(sharedLitter.expires_at) }} · fait avec La Bonne Truffe
      </p>
    </template>

    <template v-else>
      <AuthIllustrationVisual coat="inconnue" badge-icon-name="i-lucide-clock" height-class="h-[220px] md:h-[360px]" />
      <div class="flex flex-col gap-1">
        <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px]">Ce lien ne marche plus</h1>
        <p class="m-0 text-[15px] text-ink-muted md:text-lg">
          {{ loadError }} Demande à la personne qui te l’a envoyé de t’en partager un nouveau.
        </p>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import type { AsyncData, NuxtError } from '#app'
import type { ComputedRef } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { SharedLitter } from '~/types/api'
import { computed } from 'vue'
import { SharesService } from '~/services/sharesService'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterSharePresentation } from '~/utils/litterSharePresentation'

definePageMeta({ layout: 'signed-out', isPublicScreen: true })

const route: RouteLocationNormalizedLoaded = useRoute()

const token: string = String(route.params['token'])
const sharedLitterRequest: AsyncData<SharedLitter | undefined, NuxtError<unknown> | undefined> = useAsyncData(
  `shared-litter-${token}`,
  (): Promise<SharedLitter> => SharesService.read(token),
)
await sharedLitterRequest

const sharedLitter: ComputedRef<SharedLitter | null> = computed(
  (): SharedLitter | null => sharedLitterRequest.data.value ?? null,
)
const loadError: ComputedRef<string | null> = computed(
  (): string | null => sharedLitterRequest.error.value?.message ?? null,
)
const sharerInitial: ComputedRef<string> = computed(
  (): string => sharedLitter.value?.sharer_name.trim().charAt(0).toUpperCase() ?? '',
)
const birthLabel: ComputedRef<string | null> = computed((): string | null =>
  sharedLitter.value ? LitterSharePresentation.buildBirthLabel(sharedLitter.value.litter) : null,
)

useSeoMeta({
  title: (): string =>
    sharedLitter.value ? `${sharedLitter.value.litter.name} · La Bonne Truffe` : 'Portée partagée · La Bonne Truffe',
  ogTitle: (): string =>
    sharedLitter.value
      ? LitterSharePresentation.buildTitle(sharedLitter.value.sharer_name)
      : 'Une portée partagée sur La Bonne Truffe',
  ogDescription: (): string =>
    sharedLitter.value
      ? `${sharedLitter.value.litter.name} · ${LitterSharePresentation.buildSummaryLine(sharedLitter.value.litter)}`
      : '',
  ogImage: (): string => sharedLitter.value?.litter.photos[0] ?? '',
})
</script>
