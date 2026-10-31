<template>
  <div class="flex">
    <button
      type="button"
      aria-haspopup="dialog"
      :aria-expanded="isDrawerOpen"
      class="inline-flex min-h-9 items-center gap-1.5 self-start rounded-full border-0 bg-transparent px-1 text-[13px] font-extrabold text-ink-muted md:min-h-11 md:text-sm"
      @click="isDrawerOpen = true"
    >
      <UIcon name="i-lucide-arrow-up-down" class="size-4" />
      {{ selectedOption.label }}
      <UIcon name="i-lucide-chevron-down" class="size-3.5" />
    </button>
    <LitterSortDrawer v-model:open="isDrawerOpen" />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { LitterSortOption } from '~/types/Litter'
import { computed, ref } from 'vue'
import { DEFAULT_LITTER_SORT_OPTION, LITTER_SORT_OPTIONS } from '~/constants/litterSortOptions'

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const isDrawerOpen: Ref<boolean> = ref(false)

const selectedOption: ComputedRef<LitterSortOption> = computed(
  (): LitterSortOption =>
    LITTER_SORT_OPTIONS.find((option: LitterSortOption): boolean => option.key === littersStore.selectedSortKey) ??
    DEFAULT_LITTER_SORT_OPTION,
)
</script>
