<template>
  <UiDialog
    :open="props.open"
    title="Trier les portées"
    description="L’ordre reste le même jusqu’à ce que tu le changes."
    has-cream-background
    :drawer-ui="{
      content: 'min-h-[78dvh] rounded-t-3xl bg-cream md:mx-auto md:min-h-0 md:w-full md:max-w-md',
      container: 'flex flex-1 flex-col gap-6 px-5 pt-3 pb-8 md:px-8',
      body: 'flex flex-1 flex-col',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body="{ isShownAsWindow }">
      <div class="flex flex-1 flex-col gap-6">
        <LitterSortOptions @choose="chooseSort" />
        <button
          v-if="!isShownAsWindow"
          type="button"
          class="mt-auto min-h-12 self-center border-0 bg-transparent px-2 text-[15px] font-extrabold text-ink-secondary"
          @click="emit('update:open', false)"
        >
          Fermer
        </button>
      </div>
    </template>
  </UiDialog>
</template>

<script lang="ts" setup>
import type { LitterSortKey } from '~/types/Litter'
import type { LitterSortDialogEmits, LitterSortDialogProps } from '~/types/LitterSortDialog'

const props: LitterSortDialogProps = defineProps({
  open: { type: Boolean, required: true },
})

const emit: LitterSortDialogEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

/**
 * Apply a sort and close the dialog.
 *
 * @param sortKey - The sort chosen.
 */
function chooseSort(sortKey: LitterSortKey): void {
  littersStore.selectSort(sortKey)
  emit('update:open', false)
}
</script>
