<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <header class="flex shrink-0 items-start justify-between gap-4 px-5 pt-4 md:px-8 md:pt-9 lg:max-w-5xl lg:px-10">
      <div class="flex min-w-0 flex-col gap-0.5 md:gap-1">
        <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px]">{{ props.title }}</h1>
        <p v-if="props.subtitle" class="m-0 text-[15px] text-ink-muted md:text-lg">{{ props.subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>
    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="px-5 pt-5 pb-6 md:px-8 md:pt-7 md:pb-8 lg:max-w-5xl lg:px-10">
        <slot />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { UiTabScreenProps } from '~/types/UiTabScreen'

const props: UiTabScreenProps = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
