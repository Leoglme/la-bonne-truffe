<template>
  <div role="radiogroup" aria-label="Ordre des portées" class="flex flex-col gap-3">
    <button
      v-for="option in LITTER_SORT_OPTIONS"
      :key="option.key"
      type="button"
      role="radio"
      :aria-checked="option.key === littersStore.selectedSortKey"
      class="flex min-h-[68px] items-center justify-between gap-3 rounded-tile-compact border-0 bg-card px-4 text-start text-ink shadow-card"
      :class="option.key === littersStore.selectedSortKey ? 'outline-2 outline-coral' : ''"
      @click="emit('choose', option.key)"
    >
      <span class="flex flex-col">
        <span class="text-[15px] font-bold">{{ option.label }}</span>
        <span class="text-[13px] text-ink-muted">{{ option.description }}</span>
      </span>
      <span
        aria-hidden="true"
        class="inline-flex size-[22px] shrink-0 items-center justify-center rounded-full"
        :class="option.key === littersStore.selectedSortKey ? 'bg-coral text-white' : 'border-2 border-switch-off'"
      >
        <UIcon v-if="option.key === littersStore.selectedSortKey" name="i-lucide-check" class="size-3.5" />
      </span>
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { LitterSortKey } from '~/types/Litter'
import type { LitterSortOptionsEmits } from '~/types/LitterSortOptions'
import { LITTER_SORT_OPTIONS } from '~/constants/litterSortOptions'

const emit: LitterSortOptionsEmits = defineEmits<{
  (event: 'choose', sortKey: LitterSortKey): void
}>()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
</script>
