<template>
  <section class="relative flex min-h-0 min-w-0 flex-1 flex-col" aria-label="Éleveurs">
    <header class="flex shrink-0 items-center justify-between px-5 pt-4 md:px-8 md:pt-9 lg:hidden">
      <UiAppLogo />
      <div class="flex items-center gap-3">
        <NotificationBellButton />
        <span
          aria-hidden="true"
          class="hidden size-[52px] items-center justify-center rounded-full bg-avatar font-display text-xl font-semibold md:inline-flex"
        >
          <ClientOnly>{{ userInitial }}</ClientOnly>
        </span>
      </div>
    </header>

    <div
      ref="scroller"
      class="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-5 pt-5 pb-6 md:gap-6 md:px-8 md:pt-7 md:pb-8 lg:gap-[22px] lg:pt-9 lg:pr-9 lg:pb-9 lg:pl-10"
    >
      <div class="flex shrink-0 items-end justify-between gap-4">
        <div class="flex flex-col gap-0.5 md:gap-1">
          <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px] lg:text-4xl">Éleveurs</h1>
          <p class="m-0 text-[15px] text-ink-muted md:text-lg lg:text-[17px]">{{ subtitle }}</p>
        </div>
        <NuxtLink
          to="/eleveurs/recherche"
          aria-label="Rechercher un éleveur"
          class="hidden min-h-[50px] w-[360px] shrink-0 items-center gap-3 rounded-full bg-card px-5 text-base font-semibold text-ink-label no-underline shadow-card hover:text-ink-label lg:flex"
        >
          <UIcon name="i-lucide-search" class="size-5 shrink-0 text-ink" />
          Un éleveur, un affixe, une ville…
        </NuxtLink>
      </div>

      <NuxtLink
        to="/eleveurs/recherche"
        aria-label="Rechercher un éleveur"
        class="flex min-h-[52px] shrink-0 items-center gap-3 rounded-full bg-card px-5 text-[17px] font-semibold text-ink-label no-underline shadow-card hover:text-ink-label md:min-h-[58px] lg:hidden"
      >
        <UIcon name="i-lucide-search" class="size-[22px] shrink-0 text-ink" />
        Un éleveur, un affixe, une ville…
      </NuxtLink>

      <div class="flex shrink-0 flex-col gap-2 xl:flex-row xl:items-center xl:justify-between xl:gap-4">
        <BreederFilterChips />
        <BreederSortButton />
      </div>

      <p v-if="breedersStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ breedersStore.loadError }}
      </p>
      <UiEmptyStateCard
        v-else-if="!breedersStore.isLoading && breedersStore.cards.length === 0"
        title="Aucun élevage connu"
        description="Les éleveurs de tes départements arrivent avec les relevés. Tu peux aussi en ajouter un à la main."
      >
        <template #illustration>
          <UiCustomIcon name="house" :size-in-pixels="36" :stroke-width="2" class="shrink-0 text-coral" />
        </template>
      </UiEmptyStateCard>
      <div
        v-else-if="breedersStore.isLoading && breedersStore.cards.length === 0"
        aria-busy="true"
        aria-label="Chargement des éleveurs"
        class="flex flex-col gap-3.5 md:grid md:grid-cols-2 md:gap-[18px] xl:grid-cols-3"
      >
        <USkeleton v-for="placeholder in 3" :key="placeholder" class="h-[118px] rounded-card-compact md:h-[220px]" />
      </div>
      <div
        v-else-if="breedersStore.visibleCards.length === 0"
        class="flex items-center gap-4 rounded-card-compact border-2 border-dashed border-line-strong px-[22px] py-5 text-base text-ink-muted"
      >
        <UiCustomIcon name="truffle" :size-in-pixels="38" class="shrink-0 text-line-strong" />
        <span>Aucun élevage avec ce filtre.</span>
      </div>
      <template v-else>
        <div class="flex flex-col gap-3.5 md:hidden">
          <BreederRowCard v-for="breeder in breedersStore.visibleCards" :key="breeder.id" :breeder="breeder" />
        </div>
        <div class="hidden grid-cols-2 gap-[18px] md:grid xl:grid-cols-3 2xl:grid-cols-4">
          <BreederGridCard v-for="breeder in breedersStore.visibleCards" :key="breeder.id" :breeder="breeder" />
        </div>
      </template>

      <NuxtLink
        to="/eleveurs/nouveau"
        class="inline-flex min-h-11 items-center gap-1.5 self-start text-[15px] font-extrabold text-coral-text no-underline"
      >
        <UIcon name="i-lucide-plus" class="size-[18px]" />
        Ajouter un éleveur à la main
      </NuxtLink>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { UseScrollRestorationReturn } from '~/types/Composables'
import { computed, onMounted } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

useHead({ title: 'Éleveurs · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()
const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
const { scroller }: UseScrollRestorationReturn = useScrollRestoration()

const userInitial: ComputedRef<string> = computed((): string => userStore.firstName.charAt(0).toUpperCase())
const subtitle: ComputedRef<string> = computed((): string => {
  if (breedersStore.isLoading && breedersStore.cards.length === 0) {
    return ''
  }
  return BreederPresentation.buildSubtitle(breedersStore.cards)
})

onMounted(async (): Promise<void> => {
  breedersStore.restoreSavedChoices()
  await breedersStore.load()
})
</script>
