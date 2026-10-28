import type { ServiceWorkerMessage } from '~/types/Browser'

/** Opens inside the app the page of a notification tapped while a window is open, as the service worker relays it. */
export default defineNuxtPlugin((): void => {
  if (!('serviceWorker' in navigator)) {
    return
  }
  navigator.serviceWorker.addEventListener('message', (event: MessageEvent): void => {
    const message: ServiceWorkerMessage = event.data ?? {}
    if (message.type === 'notification-navigate' && typeof message.url === 'string' && message.url) {
      navigateTo(message.url)
    }
  })
})
