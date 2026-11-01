<template>
  <UModal
    v-if="isWideScreen"
    :open="props.open"
    :title="props.title"
    :description="props.description"
    :close="{
      color: 'neutral',
      variant: 'solid',
      class: 'size-11 justify-center rounded-full bg-card text-ink shadow-floating hover:bg-card',
    }"
    :ui="{
      overlay: 'bg-ink/40',
      content: [
        'divide-y-0 rounded-card shadow-[0_24px_64px_rgba(43,36,32,0.28)]',
        props.isWideWindow ? 'max-w-[900px]' : 'max-w-[480px]',
        props.hasCreamBackground ? 'bg-cream' : 'bg-card',
      ],
      header: 'min-h-0 items-start px-8 pt-7 pe-20 pb-0 sm:px-8 sm:pe-20',
      title: 'font-display text-[26px] leading-[1.15] font-semibold text-ink',
      description: 'mt-1 text-[15px] text-ink-muted',
      close: 'top-6 end-6',
      body: 'px-8 pt-5 pb-8 sm:px-8 sm:pt-5 sm:pb-8',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <slot name="body" :is-shown-as-window="true" />
    </template>
  </UModal>
  <UDrawer
    v-else
    :open="props.open"
    :title="props.title"
    :description="props.description"
    :ui="props.drawerUi"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <slot name="body" :is-shown-as-window="false" />
    </template>
  </UDrawer>
</template>

<script lang="ts" setup>
import type { DrawerProps } from '@nuxt/ui'
import type { PropType, Ref } from 'vue'
import type { UiDialogEmits, UiDialogProps } from '~/types/UiDialog'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { WIDE_SCREEN_MEDIA_QUERY } from '~/constants/mainNavigation'

const props: UiDialogProps = defineProps({
  open: { type: Boolean, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  isWideWindow: { type: Boolean, default: false },
  hasCreamBackground: { type: Boolean, default: false },
  drawerUi: { type: Object as PropType<DrawerProps['ui']>, required: true },
})

const emit: UiDialogEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const isWideScreen: Ref<boolean> = ref(false)
let wideScreenCondition: MediaQueryList | null = null

/**
 * Follow the width of the window: a window in the middle of a wide screen, a drawer from the bottom below it.
 *
 * @param event - The change of the media query.
 */
function followScreenWidth(event: MediaQueryListEvent): void {
  isWideScreen.value = event.matches
}

onMounted((): void => {
  wideScreenCondition = window.matchMedia(WIDE_SCREEN_MEDIA_QUERY)
  isWideScreen.value = wideScreenCondition.matches
  wideScreenCondition.addEventListener('change', followScreenWidth)
})

onBeforeUnmount((): void => {
  wideScreenCondition?.removeEventListener('change', followScreenWidth)
})
</script>
