import type { ServiceWorkerMessage } from '~/types/Browser'
import type { UseAppRefreshReturn } from '~/types/Composables'

/** Reloads the screens on a push received while a window is open, and opens the page of a tapped notification. */
export default defineNuxtPlugin((): void => {
  if (!('serviceWorker' in navigator)) {
    return
  }
  const { refreshAfterNews }: UseAppRefreshReturn = useAppRefresh()

  /**
   * Open the page of a tapped notification, then show what is new.
   *
   * @param url - The page the notification opens.
   */
  async function openNotificationPage(url: string): Promise<void> {
    await navigateTo(url)
    await refreshAfterNews()
  }

  navigator.serviceWorker.addEventListener('message', (event: MessageEvent): void => {
    const message: ServiceWorkerMessage = event.data ?? {}
    if (message.type === 'notification-received') {
      refreshAfterNews()
      return
    }
    if (message.type === 'notification-navigate' && typeof message.url === 'string' && message.url) {
      openNotificationPage(message.url)
    }
  })
})
