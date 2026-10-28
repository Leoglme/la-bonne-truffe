<template>
  <NuxtLink
    to="/notifications"
    :aria-label="accessibleLabel"
    class="relative inline-flex size-11 items-center justify-center rounded-full bg-card text-ink shadow-floating hover:text-ink md:size-[52px]"
  >
    <UiMockupIcon name="bell" :size-in-pixels="22" :stroke-width="2" class="size-5 md:size-[22px]" />
    <span
      v-if="bellStore.unreadCount > 0"
      class="absolute top-[9px] right-2.5 size-[9px] rounded-full border-2 border-card bg-coral md:top-3 md:right-[13px] md:size-2.5"
      aria-hidden="true"
    />
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import { computed, onMounted } from 'vue'

const bellStore: ReturnType<typeof useBellStore> = useBellStore()

const accessibleLabel: ComputedRef<string> = computed((): string => {
  const count: number = bellStore.unreadCount
  if (count === 0) {
    return 'Notifications'
  }
  return count === 1 ? 'Notifications, 1 nouvelle' : `Notifications, ${count} nouvelles`
})

onMounted((): void => {
  void bellStore.load()
})
</script>
