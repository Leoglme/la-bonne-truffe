<template>
  <NuxtLink
    :to="to"
    class="flex min-h-14 items-center justify-between gap-3 rounded-card-compact bg-card px-[22px] py-4 text-ink no-underline shadow-card hover:text-ink"
  >
    <span class="flex flex-col">
      <span class="text-[17px] font-bold">{{ title }}</span>
      <span class="text-sm text-ink-muted">{{ description }}</span>
    </span>
    <UiMockupIcon name="chevron-right" :size-in-pixels="22" :stroke-width="2.4" class="shrink-0 text-coral-text" />
  </NuxtLink>
</template>

<script lang="ts" setup>
/** A settings entry leading to its own screen, in the card style of the mockup. */
defineProps({
  to: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>
