<template>
  <div
    role="group"
    aria-label="Filtrer les éleveurs"
    class="-mx-5 flex [scrollbar-width:none] gap-1.5 overflow-x-auto px-5 md:mx-0 md:flex-wrap md:gap-2 md:overflow-visible md:px-0"
  >
    <button
      v-for="filter in BREEDER_FILTER_OPTIONS"
      :key="filter.key"
      type="button"
      :aria-pressed="breedersStore.selectedFilterKey === filter.key"
      class="relative min-h-9 shrink-0 rounded-full px-3 text-[13px] font-extrabold whitespace-nowrap shadow-chip after:absolute after:inset-x-0 after:-inset-y-1 after:content-[''] md:min-h-11 md:px-[18px] md:text-[15px]"
      :class="breedersStore.selectedFilterKey === filter.key ? 'bg-ink text-cream' : 'bg-card text-ink-secondary'"
      @click="breedersStore.selectFilter(filter.key)"
    >
      {{ filter.label }}
    </button>
  </div>
</template>

<script lang="ts" setup>
import { BREEDER_FILTER_OPTIONS } from '~/constants/breederOptions'

const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
</script>
