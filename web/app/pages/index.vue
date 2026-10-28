<template>
  <div class="flex flex-col gap-5 px-5 pt-[58px] pb-6 md:gap-7 md:px-8 md:pt-9 md:pb-8 lg:px-10">
    <div class="flex items-center justify-between gap-3">
      <div class="lg:invisible">
        <UiAppLogo />
      </div>
      <div class="flex items-center gap-3">
        <NotificationBellButton />
        <span
          :aria-label="userStore.firstName"
          class="hidden size-[52px] items-center justify-center rounded-full bg-avatar font-display text-xl font-semibold md:inline-flex"
        >
          {{ userInitial }}
        </span>
      </div>
    </div>

    <UiPageHeader
      :title="greeting"
      subtitle="Aucune portée pour l’instant : elles arriveront ici dès le premier relevé des sources."
    />

    <section class="flex flex-col gap-4" aria-labelledby="litters-heading">
      <div class="flex flex-wrap items-center justify-between gap-x-2 gap-y-3">
        <h2 id="litters-heading" class="m-0 font-display text-xl font-semibold whitespace-nowrap md:text-2xl">
          Les portées
        </h2>
        <div role="group" aria-label="Filtrer" class="flex gap-1.5 md:gap-2">
          <button
            v-for="filter in LITTER_FILTERS"
            :key="filter.key"
            type="button"
            :aria-pressed="selectedFilterKey === filter.key"
            class="min-h-11 rounded-full px-3 text-[13px] font-extrabold whitespace-nowrap shadow-floating md:px-[18px] md:text-[15px]"
            :class="selectedFilterKey === filter.key ? 'bg-ink text-cream' : 'bg-card text-ink-secondary'"
            @click="selectedFilterKey = filter.key"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <UiEmptyStateCard
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
    </section>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref } from 'vue'

type LitterFilterKey = 'all' | 'preferred' | 'expected'

const LITTER_FILTERS: readonly { key: LitterFilterKey; label: string }[] = [
  { key: 'all', label: 'Toutes' },
  { key: 'preferred', label: 'Préférées' },
  { key: 'expected', label: 'À naître' },
]

useHead({ title: 'Portées · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()

const selectedFilterKey: Ref<LitterFilterKey> = ref('all')

const greeting: ComputedRef<string> = computed((): string =>
  userStore.firstName ? `Bonjour ${userStore.firstName}` : 'Bonjour',
)
const userInitial: ComputedRef<string> = computed((): string => userStore.firstName.charAt(0).toUpperCase())
</script>
