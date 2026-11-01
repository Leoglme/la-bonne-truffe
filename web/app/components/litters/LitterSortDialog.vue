<template>
  <UModal
    v-if="isWideScreen"
    :open="props.open"
    title="Trier les portées"
    description="L’ordre reste le même jusqu’à ce que tu le changes."
    :close="{
      color: 'neutral',
      variant: 'solid',
      class: 'size-11 justify-center rounded-full bg-card text-ink shadow-floating hover:bg-card',
    }"
    :ui="{
      overlay: 'bg-ink/40',
      content: 'max-w-[480px] divide-y-0 rounded-card bg-cream shadow-[0_24px_64px_rgba(43,36,32,0.28)]',
      header: 'min-h-0 items-start px-7 pt-[26px] pb-0 sm:px-7',
      title: 'font-display text-[26px] leading-[1.15] font-semibold text-ink',
      description: 'mt-1 text-[15px] text-ink-muted',
      close: 'top-[22px] end-6',
      body: 'px-7 pt-5 pb-7 sm:px-7 sm:pt-5 sm:pb-7',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <LitterSortOptions @choose="chooseSort" />
    </template>
  </UModal>
  <UDrawer
    v-else
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
        <LitterSortOptions @choose="chooseSort" />
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
import type { Ref } from 'vue'
import type { LitterSortKey } from '~/types/Litter'
import type { LitterSortDialogEmits, LitterSortDialogProps } from '~/types/LitterSortDialog'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { SIDE_PANEL_MEDIA_QUERY } from '~/constants/mainNavigation'

const props: LitterSortDialogProps = defineProps({
  open: { type: Boolean, required: true },
})

const emit: LitterSortDialogEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const isWideScreen: Ref<boolean> = ref(false)
let wideScreenCondition: MediaQueryList | null = null

/**
 * Apply a sort and close the dialog.
 *
 * @param sortKey - The sort chosen.
 */
function chooseSort(sortKey: LitterSortKey): void {
  littersStore.selectSort(sortKey)
  emit('update:open', false)
}

/**
 * Follow the width of the window: a window in the middle of a wide screen, a drawer from the bottom below it.
 *
 * @param event - The change of the media query.
 */
function followScreenWidth(event: MediaQueryListEvent): void {
  isWideScreen.value = event.matches
}

onMounted((): void => {
  wideScreenCondition = window.matchMedia(SIDE_PANEL_MEDIA_QUERY)
  isWideScreen.value = wideScreenCondition.matches
  wideScreenCondition.addEventListener('change', followScreenWidth)
})

onBeforeUnmount((): void => {
  wideScreenCondition?.removeEventListener('change', followScreenWidth)
})
</script>
