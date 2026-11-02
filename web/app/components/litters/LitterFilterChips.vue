<template>
  <div role="group" aria-label="Filtrer" class="flex grow gap-1.5 md:gap-2 lg:grow-0">
    <button
      v-for="filter in LITTER_FILTER_OPTIONS"
      :key="filter.key"
      type="button"
      :aria-pressed="littersStore.selectedFilterKey === filter.key"
      class="relative min-h-9 flex-1 rounded-full px-3 text-[13px] font-extrabold whitespace-nowrap shadow-chip after:absolute after:inset-x-0 after:-inset-y-1 after:content-[''] md:min-h-11 md:px-[18px] md:text-[15px] lg:flex-none"
      :class="littersStore.selectedFilterKey === filter.key ? 'bg-ink text-cream' : 'bg-card text-ink-secondary'"
      @click="littersStore.selectFilter(filter.key)"
    >
      {{ filter.label }}
    </button>
  </div>
</template>

<script lang="ts" setup>
import { LITTER_FILTER_OPTIONS } from '~/constants/litterFilterOptions'

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
</script>
