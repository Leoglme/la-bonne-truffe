import type { Ref } from 'vue'
import type { NotificationHistory, SentNotification } from '~/types/api'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { NotificationsService } from '~/services/notificationsService'

/** Pinia store of the bell: notification history and the unread count that lights the coral dot. */
// Pinia ne fournit pas de type nommé pour un store : TypeScript l'élide, il est inécrivable.
// eslint-disable-next-line @typescript-eslint/typedef
export const useBellStore = defineStore('bell', () => {
  const notifications: Ref<SentNotification[]> = ref([])
  const unreadCount: Ref<number> = ref(0)

  /**
   * Load the latest notifications and the unread count; a failure leaves the bell unlit.
   */
  async function load(): Promise<void> {
    try {
      const history: NotificationHistory = await NotificationsService.getHistory()
      notifications.value = history.items
      unreadCount.value = history.unread_count
    } catch {
      unreadCount.value = 0
    }
  }

  /**
   * Mark everything as read once the history is opened.
   */
  async function markAllRead(): Promise<void> {
    await NotificationsService.markAllRead()
    unreadCount.value = 0
  }

  return { notifications, unreadCount, load, markAllRead }
})
