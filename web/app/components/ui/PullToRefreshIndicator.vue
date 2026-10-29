<template>
  <div
    v-if="props.pullDistanceInPixels > 0"
    :role="props.isRefreshing ? 'status' : undefined"
    class="pointer-events-none absolute inset-x-0 top-0 z-30 flex justify-center"
    :style="{ transform: `translateY(${props.pullDistanceInPixels - INDICATOR_SIZE_IN_PIXELS}px)` }"
  >
    <span
      class="inline-flex size-10 items-center justify-center rounded-full bg-card shadow-floating"
      :class="props.isReadyToRefresh ? 'text-coral' : 'text-ink-muted'"
    >
      <UIcon v-if="props.isRefreshing" name="i-lucide-loader-circle" class="size-5 animate-spin" />
      <UIcon
        v-else
        name="i-lucide-arrow-down"
        class="size-5 transition-transform duration-200"
        :class="{ 'rotate-180': props.isReadyToRefresh }"
      />
      <span v-if="props.isRefreshing" class="sr-only">Actualisation…</span>
    </span>
  </div>
</template>

<script lang="ts" setup>
import type { UiPullToRefreshIndicatorProps } from '~/types/UiPullToRefreshIndicator'

const props: UiPullToRefreshIndicatorProps = defineProps({
  pullDistanceInPixels: { type: Number, required: true },
  isReadyToRefresh: { type: Boolean, required: true },
  isRefreshing: { type: Boolean, required: true },
})

const INDICATOR_SIZE_IN_PIXELS: number = 40
</script>
