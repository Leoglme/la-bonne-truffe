<template>
  <NuxtLink
    :to="props.to"
    class="flex min-h-14 items-center justify-between gap-3 rounded-card-compact bg-card px-[22px] py-4 text-ink no-underline shadow-card hover:text-ink"
  >
    <span class="flex flex-col">
      <span class="text-[17px] font-bold">{{ props.title }}</span>
      <span class="text-sm text-ink-muted">{{ props.description }}</span>
    </span>
    <UIcon name="i-lucide-chevron-right" class="size-[22px] shrink-0 text-coral-text" />
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { UiLinkCardProps } from '~/types/UiLinkCard'

const props: UiLinkCardProps = defineProps({
  to: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>
