<template>
  <div class="flex min-h-0 flex-1">
    <section class="relative flex min-h-0 min-w-0 flex-1 flex-col" aria-label="Portées">
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
        class="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-5 pt-5 pb-6 md:gap-7 md:px-8 md:pt-7 md:pb-8 lg:gap-[26px] lg:pt-9 lg:pr-9 lg:pb-9 lg:pl-10"
      >
        <div class="flex shrink-0 items-end justify-between gap-4">
          <div class="flex flex-col gap-0.5 md:gap-1 lg:gap-0.5">
            <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px] lg:text-4xl">
              <ClientOnly fallback="Bonjour">{{ greeting }}</ClientOnly>
            </h1>
            <p class="m-0 text-[15px] text-ink-muted md:text-lg lg:text-[17px]">{{ greetingSubtitle }}</p>
          </div>
          <div class="hidden shrink-0 flex-col items-end gap-1 lg:flex">
            <LitterFilterChips />
            <LitterSortButton />
          </div>
        </div>

        <HomeBornLastNightCard v-if="bornLastNightLitter" :litter="bornLastNightLitter" />

        <div class="flex shrink-0 flex-col gap-5 md:gap-4">
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between lg:hidden">
            <h2 class="m-0 font-display text-xl font-semibold whitespace-nowrap md:text-2xl">Les portées</h2>
            <LitterFilterChips />
          </div>
          <LitterSortButton class="-mt-2 lg:hidden" />

          <p v-if="littersStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
            {{ littersStore.loadError }}
          </p>
          <UiEmptyStateCard
            v-else-if="!littersStore.isLoading && littersStore.visibleCards.length === 0"
            title="La truffe n’a encore rien flairé"
            description="Les portées qui te correspondent s’afficheront ici, les préférées en premier."
          >
            <template #illustration>
              <span
                class="inline-flex size-[118px] shrink-0 items-center justify-center rounded-tile-compact bg-gold-pastel"
              >
                <CockerIllustration coat="gold" :size-in-pixels="84" />
              </span>
            </template>
          </UiEmptyStateCard>
          <div
            v-else-if="littersStore.isLoading && littersStore.cards.length === 0"
            aria-busy="true"
            aria-label="Chargement des portées"
            class="flex flex-col gap-3.5 md:grid md:grid-cols-2 md:gap-5 xl:grid-cols-3"
          >
            <USkeleton
              v-for="placeholder in 3"
              :key="placeholder"
              class="h-[142px] rounded-card-compact md:h-[300px] md:rounded-card"
            />
          </div>

          <div class="flex flex-col gap-3.5 md:hidden">
            <template v-for="litter in littersStore.visibleCards" :key="litter.id">
              <UiUpToDateSeparator v-if="litter.id === firstAlreadySeenLitterId" class="my-1.5" />
              <LitterRowCard
                :litter="litter"
                :is-new="LitterPresentation.isNew(litter, littersStore.previousVisitAt)"
              />
            </template>
          </div>
          <div
            class="hidden grid-cols-2 gap-5 md:grid"
            :class="littersStore.selectedLitter ? 'xl:grid-cols-2' : 'xl:grid-cols-3 2xl:grid-cols-4'"
          >
            <template v-for="litter in littersStore.visibleCards" :key="litter.id">
              <UiUpToDateSeparator v-if="litter.id === firstAlreadySeenLitterId" class="col-span-full" />
              <LitterGridCard
                :litter="litter"
                :is-new="LitterPresentation.isNew(litter, littersStore.previousVisitAt)"
                :is-selected="littersStore.selectedLitter?.id === litter.id"
                @activate="(clickEvent: MouseEvent): Promise<void> => openInSidePanel(clickEvent, litter.id)"
              />
            </template>
          </div>
        </div>
      </div>
      <NuxtLink
        to="/carte"
        aria-label="Voir les portées sur la carte"
        class="absolute right-5 bottom-5 inline-flex size-14 items-center justify-center rounded-full bg-ink text-cream no-underline shadow-straddling-photo hover:text-cream md:right-8 md:bottom-8"
      >
        <UIcon name="i-lucide-map" class="size-6" />
      </NuxtLink>
    </section>

    <LitterDetailPanel
      v-if="littersStore.selectedLitter"
      :litter="littersStore.selectedLitter"
      class="hidden xl:flex"
      @close="littersStore.clearSelection()"
    />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { LitterCard } from '~/types/api'
import { computed, onMounted } from 'vue'
import { LitterPresentation } from '~/utils/litterPresentation'

useHead({ title: 'Portées · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()
const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const SIDE_PANEL_MEDIA_QUERY: string = '(min-width: 1280px)'

const greeting: ComputedRef<string> = computed((): string =>
  userStore.firstName ? `Bonjour ${userStore.firstName}` : 'Bonjour',
)
const userInitial: ComputedRef<string> = computed((): string => userStore.firstName.charAt(0).toUpperCase())
const greetingSubtitle: ComputedRef<string> = computed((): string => {
  if (littersStore.isLoading && littersStore.cards.length === 0) {
    return ''
  }
  return LitterPresentation.buildGreetingSubtitle(
    littersStore.preferredCards.length,
    littersStore.bornLastNightCards.length,
  )
})
const bornLastNightLitter: ComputedRef<LitterCard | null> = computed(
  (): LitterCard | null => littersStore.bornLastNightCards[0] ?? null,
)
const firstAlreadySeenLitterId: ComputedRef<number | null> = computed((): number | null =>
  littersStore.previousVisitAt === null ? null : (littersStore.alreadySeenCards[0]?.id ?? null),
)

/**
 * Whether the screen is wide enough for the side panel that shows the selected litter.
 *
 * @returns True on a wide desktop.
 */
function isSidePanelShown(): boolean {
  return window.matchMedia(SIDE_PANEL_MEDIA_QUERY).matches
}

/**
 * On a wide desktop, show the litter in the side panel instead of leaving the list.
 *
 * @param clickEvent - The click on the card.
 * @param litterId - The litter.
 */
async function openInSidePanel(clickEvent: MouseEvent, litterId: number): Promise<void> {
  if (!isSidePanelShown()) {
    return
  }
  clickEvent.preventDefault()
  await littersStore.select(litterId)
}

onMounted(async (): Promise<void> => {
  littersStore.restoreSavedSort()
  await Promise.all([littersStore.recordVisit(), littersStore.load()])
})
</script>
