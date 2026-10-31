<template>
  <button
    type="button"
    class="inline-flex min-h-11 items-center gap-1 self-start border-0 bg-transparent px-0 text-sm font-bold text-ink-muted"
    :aria-label="`Trier : ${currentSortLabel}. Changer le tri`"
    @click="selectNextSort"
  >
    {{ currentSortLabel }}
    <UIcon name="i-lucide-chevron-down" class="size-4" />
  </button>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { BreederSortOption } from '~/types/Breeder'
import { computed } from 'vue'
import { BREEDER_SORT_OPTIONS } from '~/constants/breederOptions'

const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()

const currentSortIndex: ComputedRef<number> = computed((): number =>
  Math.max(
    0,
    BREEDER_SORT_OPTIONS.findIndex(
      (option: BreederSortOption): boolean => option.key === breedersStore.selectedSortKey,
    ),
  ),
)
const currentSortLabel: ComputedRef<string> = computed(
  (): string => BREEDER_SORT_OPTIONS[currentSortIndex.value]?.label ?? '',
)

/**
 * Go to the next sort of the list, round and round.
 */
function selectNextSort(): void {
  const nextOption: BreederSortOption | undefined =
    BREEDER_SORT_OPTIONS[(currentSortIndex.value + 1) % BREEDER_SORT_OPTIONS.length]
  if (nextOption !== undefined) {
    breedersStore.selectSort(nextOption.key)
  }
}
</script>
