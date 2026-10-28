<template>
  <NuxtLink
    to="/reglages/notifications"
    :aria-label="accessibleLabel"
    class="relative inline-flex size-11 items-center justify-center rounded-full bg-card text-ink shadow-floating hover:text-ink md:size-[52px]"
  >
    <UIcon name="i-lucide-bell" class="size-5 md:size-[22px]" aria-hidden="true" />
    <span
      v-if="unreadCount > 0"
      class="absolute top-[9px] right-2.5 size-[9px] rounded-full border-2 border-card bg-coral md:top-3 md:right-[13px] md:size-2.5"
      aria-hidden="true"
    />
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { NotificationHistory } from '~/types/api'
import { computed, onMounted, ref } from 'vue'
import { NotificationsService } from '~/services/notificationsService'

const unreadCount: Ref<number> = ref(0)

const accessibleLabel: ComputedRef<string> = computed((): string => {
  if (unreadCount.value === 0) {
    return 'Notifications'
  }
  return unreadCount.value === 1 ? 'Notifications, 1 nouvelle' : `Notifications, ${unreadCount.value} nouvelles`
})

/**
 * Read the unread count that lights the coral dot. A failure leaves the bell unlit.
 */
async function loadUnreadCount(): Promise<void> {
  try {
    const history: NotificationHistory = await NotificationsService.getHistory()
    unreadCount.value = history.unread_count
  } catch {
    unreadCount.value = 0
  }
}

onMounted((): void => {
  void loadUnreadCount()
})
</script>
