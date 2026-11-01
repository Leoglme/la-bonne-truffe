<template>
  <div class="mx-auto box-border w-full max-w-[1320px] flex-col gap-6 px-10 pt-7 pb-14">
    <div class="flex items-center justify-between gap-4">
      <slot name="back" />
      <div class="flex items-center gap-3">
        <slot name="actions" />
      </div>
    </div>
    <div class="grid grid-cols-[minmax(0,1fr)_400px] items-start gap-8">
      <div class="flex min-w-0 flex-col gap-5">
        <slot />
      </div>
      <aside :aria-label="props.asideLabel" class="sticky top-6 flex flex-col gap-4">
        <slot name="aside" />
      </aside>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { UiWideDetailLayoutProps } from '~/types/UiWideDetailLayout'

const props: UiWideDetailLayoutProps = defineProps({
  asideLabel: { type: String, required: true },
})
</script>
