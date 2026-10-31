<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
    <div class="flex min-h-0 flex-1 flex-col lg:w-full lg:max-w-5xl">
      <div
        class="relative flex h-[230px] shrink-0 items-center justify-center overflow-hidden bg-gold-pastel md:h-[300px]"
      >
        <BreederCover v-if="breeder" :breeder="breeder" :illustration-size-in-pixels="200" />
        <button
          type="button"
          aria-label="Retour aux éleveurs"
          class="absolute top-4 left-5 inline-flex size-11 items-center justify-center rounded-full border-0 bg-card text-ink shadow-floating-over-photo md:top-9 md:left-8 md:size-[52px] md:shadow-floating"
          @click="goBack"
        >
          <UIcon name="i-lucide-chevron-left" class="size-5 md:size-[22px]" />
        </button>
        <BreederFollowHeartButton
          v-if="breeder"
          :breeder="breeder"
          class="absolute top-4 right-5 md:top-9 md:right-8"
        />
        <span
          v-if="heroTag"
          class="absolute bottom-11 left-5 hidden rounded-full bg-card px-4 py-1.5 text-sm leading-normal font-extrabold tracking-[0.02em] text-coral-text uppercase md:left-8 md:inline"
        >
          {{ heroTag }}
        </span>
      </div>

      <p v-if="loadError" role="alert" class="m-0 p-8 text-[15px] font-bold text-coral-text">{{ loadError }}</p>
      <div
        v-else-if="breeder"
        class="relative -mt-7 flex min-h-0 flex-1 flex-col overflow-hidden rounded-t-[28px] bg-cream md:-mt-9 md:rounded-t-[36px]"
      >
        <div
          class="flex min-h-0 flex-1 flex-col gap-[18px] overflow-y-auto px-5 pt-6 pb-4 md:gap-6 md:px-8 md:pt-8 md:pb-6"
        >
          <div class="flex shrink-0 items-center gap-3.5 md:gap-4">
            <BreederAvatarTile
              :breeder="breeder"
              size-class="size-14 rounded-[18px] md:size-[72px] md:rounded-[22px]"
              text-class="text-[22px] md:text-[26px]"
            />
            <div class="flex min-w-0 flex-col gap-0.5 md:gap-1">
              <h1 class="m-0 font-display text-2xl leading-[1.1] font-semibold md:text-[32px]">{{ breeder.name }}</h1>
              <span class="inline-flex items-center gap-1.5 text-sm text-ink-muted md:text-[17px]">
                <UiCustomIcon name="pin" :size-in-pixels="18" :stroke-width="2" class="hidden shrink-0 md:block" />
                {{ BreederPresentation.buildIdentityLine(breeder, locationStore.position) }}
              </span>
            </div>
          </div>
          <BreederChips :chips="chips" class="shrink-0" />
          <BreederStats :breeder="breeder" class="shrink-0" />
          <BreederPhotoGallery :photos="breeder.photos" class="shrink-0" />
          <BreederLittersList :breeder="breeder" class="shrink-0" />
          <BreederColorShares :breeder="breeder" class="shrink-0" />
          <BreederDogsList :breeder="breeder" class="shrink-0" />
          <BreederSeenOnList :breeder="breeder" class="shrink-0" />
          <BreederFollowCard :breeder="breeder" class="shrink-0" />
          <p
            v-if="breeder.notes"
            class="m-0 shrink-0 text-sm leading-[1.45] whitespace-pre-line text-ink-secondary md:text-[15px]"
          >
            {{ breeder.notes }}
          </p>
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
      <div
        v-else
        aria-busy="true"
        aria-label="Chargement de l’éleveur"
        class="relative -mt-7 flex min-h-0 flex-1 flex-col gap-4 rounded-t-[28px] bg-cream px-5 pt-6 md:-mt-9 md:gap-6 md:rounded-t-[36px] md:px-8 md:pt-8"
      >
        <USkeleton class="h-8 w-2/3 rounded-full" />
        <USkeleton class="h-20 w-full rounded-2xl" />
        <USkeleton class="h-20 w-full rounded-2xl" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { BreederDetail, LitterCard } from '~/types/api'
import type { BreederChip } from '~/types/Breeder'
import type { UseBackNavigationReturn } from '~/types/Composables'
import type { PrimaryAction } from '~/types/PrimaryAction'
import { computed, onMounted, ref, watch } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

definePageMeta({ isPushedScreen: true, key: 'breeder-detail' })

const route: RouteLocationNormalizedLoaded = useRoute()
const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()
const { goBack }: UseBackNavigationReturn = useBackNavigation('/eleveurs')

const loadError: Ref<string | null> = ref(null)

const breederId: ComputedRef<number> = computed((): number => Number(route.params['id']))
const breeder: ComputedRef<BreederDetail | null> = computed((): BreederDetail | null =>
  breedersStore.selectedBreeder?.id === breederId.value ? breedersStore.selectedBreeder : null,
)
const chips: ComputedRef<BreederChip[]> = computed((): BreederChip[] =>
  breeder.value === null ? [] : BreederPresentation.listDetailChips(breeder.value),
)
const heroTag: ComputedRef<string | null> = computed((): string | null => {
  const currentLitter: LitterCard | null = breeder.value?.current_litter ?? null
  if (currentLitter === null) {
    return null
  }
  return currentLitter.kind === 'litter_expected' ? 'Une portée à naître' : 'Une portée en cours'
})
const primaryAction: ComputedRef<PrimaryAction | null> = computed((): PrimaryAction | null =>
  breeder.value === null ? null : BreederPresentation.resolvePrimaryAction(breeder.value),
)
const pageTitle: ComputedRef<string> = computed((): string => `${breeder.value?.name ?? 'Éleveur'} · La Bonne Truffe`)

/**
 * Load a breeder into the screen, and say why when it cannot be read.
 *
 * @param id - The breeder.
 */
async function loadBreeder(id: number): Promise<void> {
  loadError.value = null
  try {
    await breedersStore.select(id)
  } catch (error: unknown) {
    loadError.value = error instanceof Error ? error.message : 'Éleveur introuvable'
  }
}

useHead({ title: pageTitle })

watch(breederId, async (id: number): Promise<void> => {
  if (breedersStore.selectedBreeder?.id !== id) {
    await loadBreeder(id)
  }
})

onMounted((): Promise<void> => loadBreeder(breederId.value))
</script>
