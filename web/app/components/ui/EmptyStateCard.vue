<template>
  <section
    class="flex flex-col items-center gap-4 rounded-card-compact border-2 border-dashed border-line-strong px-6 py-8 text-center md:flex-row md:text-left"
  >
    <slot name="illustration" />
    <div class="flex flex-col gap-1">
      <h2 class="m-0 font-display text-xl font-semibold md:text-[22px]">{{ props.title }}</h2>
      <p class="m-0 text-[15px] text-ink-muted md:text-base">{{ props.description }}</p>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { UiEmptyStateCardProps } from '~/types/UiEmptyStateCard'

const props: UiEmptyStateCardProps = defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>
