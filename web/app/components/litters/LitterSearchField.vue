<template>
  <div
    class="flex min-h-[52px] items-center gap-3 rounded-full border-2 border-transparent bg-card ps-5 pe-2 shadow-card focus-within:border-coral focus-within:ring-4 focus-within:ring-coral-pastel md:min-h-[58px] lg:min-h-[50px]"
  >
    <UIcon name="i-lucide-search" class="size-[22px] shrink-0 text-ink lg:size-5" />
    <label :for="searchFieldId" class="sr-only">Rechercher une portée</label>
    <input
      :id="searchFieldId"
      v-model="littersStore.searchQuery"
      type="search"
      placeholder="Éleveur, ville, département…"
      autocomplete="off"
      enterkeyhint="search"
      class="min-w-0 grow border-0 bg-transparent py-2 text-[17px] font-semibold text-ink outline-none placeholder:text-ink-label lg:text-base [&::-webkit-search-cancel-button]:hidden"
    />
    <button
      v-if="littersStore.searchQuery !== ''"
      type="button"
      aria-label="Effacer la recherche"
      class="inline-flex size-9 shrink-0 items-center justify-center rounded-full border-0 bg-chip text-ink-secondary"
      @click="littersStore.searchQuery = ''"
    >
      <UIcon name="i-lucide-x" class="size-[18px]" />
    </button>
  </div>
</template>

<script lang="ts" setup>
import { useId } from 'vue'

const searchFieldId: string = useId()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
</script>
