import type { Ref } from 'vue'
import type { NotificationHistory, SentNotification } from '~/types/api'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { NotificationsService } from '~/services/notificationsService'

/** Pinia store of the bell: notification history and the unread count that lights the coral dot. */
export const useBellStore = defineStore('bell', () => {
  const notifications: Ref<SentNotification[]> = ref([])
  const unreadCount: Ref<number> = ref(0)
  const isLoading: Ref<boolean> = ref(true)
  const loadError: Ref<string | null> = ref(null)

  /**
   * Load the latest notifications and the unread count; a failure leaves the bell unlit.
   */
  async function load(): Promise<void> {
    isLoading.value = true
    loadError.value = null
    try {
      const history: NotificationHistory = await NotificationsService.getHistory()
      notifications.value = history.items
      unreadCount.value = history.unread_count
    } catch (error: unknown) {
      unreadCount.value = 0
      loadError.value = error instanceof Error ? error.message : 'Chargement impossible'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Mark everything as read once the history is opened.
   */
  async function markAllRead(): Promise<void> {
    await NotificationsService.markAllRead()
    unreadCount.value = 0
  }

  return { notifications, unreadCount, isLoading, loadError, load, markAllRead }
})
