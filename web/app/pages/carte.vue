<template>
  <div class="relative flex min-h-0 flex-1 flex-col">
    <ClientOnly>
      <LitterMap
        v-model:selected-litter-ids="selectedLitterIds"
        class="absolute inset-0"
        :litters="littersStore.visibleCards"
        :home-position="locationStore.position"
      />
      <template #fallback>
        <USkeleton class="absolute inset-0 rounded-none" />
      </template>
    </ClientOnly>

    <div class="absolute inset-x-5 top-4 z-10 flex items-center gap-2.5 md:inset-x-8 md:top-9">
      <NuxtLink
        to="/"
        aria-label="Revenir à la liste"
        class="inline-flex size-11 shrink-0 items-center justify-center rounded-full bg-card text-ink no-underline shadow-floating-over-photo hover:text-ink md:size-[52px]"
      >
        <UIcon name="i-lucide-list" class="size-5 md:size-[22px]" />
      </NuxtLink>
      <LitterFilterChips />
    </div>

    <UiErrorAlert
      v-if="littersStore.loadError"
      :message="littersStore.loadError"
      class="absolute inset-x-5 bottom-5 z-10 shadow-card md:inset-x-8 md:bottom-8 md:max-w-md"
    />
    <div
      v-else-if="selectedLitters.length > 0"
      class="absolute inset-x-5 bottom-5 z-10 flex max-h-[46%] flex-col gap-2.5 overflow-y-auto md:inset-x-8 md:bottom-8 md:max-w-md"
    >
      <LitterRowCard
        v-for="litter in selectedLitters"
        :key="litter.id"
        :litter="litter"
        :is-new="LitterPresentation.isNew(litter, littersStore.previousVisitAt)"
        class="shadow-straddling-photo"
      />
    </div>
    <p
      v-else-if="!littersStore.isLoading && !hasLocatedLitter"
      class="absolute inset-x-5 bottom-5 z-10 m-0 rounded-2xl bg-card px-4 py-3 text-center text-[15px] text-ink-muted shadow-card md:inset-x-8 md:bottom-8 md:max-w-md"
    >
      Aucune portée n’a de position connue pour l’instant.
    </p>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { LitterCard } from '~/types/api'
import { computed, onMounted, ref } from 'vue'
import { LitterMapPlaces } from '~/utils/litterMapPlaces'
import { LitterPresentation } from '~/utils/litterPresentation'

useHead({ title: 'Carte · La Bonne Truffe' })

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const selectedLitterIds: Ref<number[]> = ref([])

const selectedLitters: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
  littersStore.visibleCards.filter((card: LitterCard): boolean => selectedLitterIds.value.includes(card.id)),
)
const hasLocatedLitter: ComputedRef<boolean> = computed(
  (): boolean => LitterMapPlaces.groupByPosition(littersStore.visibleCards).length > 0,
)

onMounted(async (): Promise<void> => {
  littersStore.restoreSavedSort()
  if (littersStore.cards.length === 0) {
    await littersStore.load()
  }
})
</script>
