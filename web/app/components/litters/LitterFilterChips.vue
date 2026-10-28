<template>
  <div role="group" aria-label="Filtrer" class="flex gap-1.5 md:gap-2">
    <button
      v-for="filter in LITTER_FILTERS"
      :key="filter.key"
      type="button"
      :aria-pressed="littersStore.selectedFilterKey === filter.key"
      class="relative min-h-9 rounded-full px-3 text-[13px] font-extrabold whitespace-nowrap shadow-chip after:absolute after:inset-x-0 after:-inset-y-1 after:content-[''] md:min-h-11 md:px-[18px] md:text-[15px]"
      :class="littersStore.selectedFilterKey === filter.key ? 'bg-ink text-cream' : 'bg-card text-ink-secondary'"
      @click="littersStore.selectedFilterKey = filter.key"
    >
      {{ filter.label }}
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { LitterFilterOption } from '~/types/Litter'

const LITTER_FILTERS: LitterFilterOption[] = [
  { key: 'all', label: 'Toutes' },
  { key: 'preferred', label: 'Préférées' },
  { key: 'expected', label: 'À naître' },
]

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
</script>
