<template>
  <UDrawer
    :open="props.open"
    title="Trier les portées"
    description="L’ordre reste le même jusqu’à ce que tu le changes."
    :ui="{
      content: 'min-h-[78dvh] rounded-t-3xl bg-cream md:mx-auto md:min-h-0 md:w-full md:max-w-md',
      container: 'flex flex-1 flex-col gap-6 px-5 pt-3 pb-8 md:px-8',
      body: 'flex flex-1 flex-col',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <div class="flex flex-1 flex-col gap-6">
        <div role="radiogroup" aria-label="Ordre des portées" class="flex flex-col gap-3">
          <button
            v-for="option in LITTER_SORT_OPTIONS"
            :key="option.key"
            type="button"
            role="radio"
            :aria-checked="option.key === littersStore.selectedSortKey"
            class="flex min-h-[68px] items-center justify-between gap-3 rounded-tile-compact border-0 bg-card px-4 text-start text-ink shadow-card"
            :class="option.key === littersStore.selectedSortKey ? 'outline-2 outline-coral' : ''"
            @click="chooseSort(option.key)"
          >
            <span class="flex flex-col">
              <span class="text-[15px] font-bold">{{ option.label }}</span>
              <span class="text-[13px] text-ink-muted">{{ option.description }}</span>
            </span>
            <span
              aria-hidden="true"
              class="inline-flex size-[22px] shrink-0 items-center justify-center rounded-full"
              :class="
                option.key === littersStore.selectedSortKey ? 'bg-coral text-white' : 'border-2 border-switch-off'
              "
            >
              <UIcon v-if="option.key === littersStore.selectedSortKey" name="i-lucide-check" class="size-3.5" />
            </span>
          </button>
        </div>
        <button
          type="button"
          class="mt-auto min-h-12 self-center border-0 bg-transparent px-2 text-[15px] font-extrabold text-ink-secondary"
          @click="emit('update:open', false)"
        >
          Fermer
        </button>
      </div>
    </template>
  </UDrawer>
</template>

<script lang="ts" setup>
import type { LitterSortKey } from '~/types/Litter'
import type { LitterSortDrawerEmits, LitterSortDrawerProps } from '~/types/LitterSortDrawer'
import { LITTER_SORT_OPTIONS } from '~/constants/litterSortOptions'

const props: LitterSortDrawerProps = defineProps({
  open: { type: Boolean, required: true },
})

const emit: LitterSortDrawerEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

/**
 * Apply a sort and close the drawer.
 *
 * @param sortKey - The sort chosen.
 */
function chooseSort(sortKey: LitterSortKey): void {
  littersStore.selectSort(sortKey)
  emit('update:open', false)
}
</script>
