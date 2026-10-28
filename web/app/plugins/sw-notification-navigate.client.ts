/**
 * Route the PWA in-app when the service worker relays a notification tap.
 *
 * The service worker posts `{ type: 'notification-navigate', url }` to an already-open window
 * instead of a hard `client.navigate` (ignored on iOS), and this listener turns it into a router
 * navigation. Copied from DevLeadHunter.
 */
export default defineNuxtPlugin((): void => {
  if (!('serviceWorker' in navigator)) {
    return
  }
  navigator.serviceWorker.addEventListener('message', (event: MessageEvent): void => {
    const message: { type?: unknown; url?: unknown } = event.data ?? {}
    if (message.type === 'notification-navigate' && typeof message.url === 'string' && message.url) {
      void navigateTo(message.url)
    }
  })
})
