import type { VapidKeyResponse } from '~/types/api'
import { NotificationsService } from '~/services/notificationsService'

/** localStorage flag: the user turned notifications off on this device, so don't auto-resubscribe. */
const PUSH_DISABLED_STORAGE_KEY: string = 'lbt-push-disabled'

/**
 * Web Push helpers shared by the settings switch (`useWebPush`) and the auto-subscribe plugin.
 * Copied from DevLeadHunter, gathered in a class.
 */
export class WebPush {
  /**
   * Whether this browser can do Web Push at all.
   *
   * @returns True when service workers, the Push API and notifications are available.
   */
  static isSupported(): boolean {
    return import.meta.client && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
  }

  /**
   * Whether the app runs as an installed PWA, which iOS requires before it delivers any push.
   *
   * @returns True in standalone display mode.
   */
  static isStandalonePwa(): boolean {
    if (!import.meta.client) {
      return false
    }
    const isIosStandalone: boolean = (window.navigator as Navigator & { standalone?: boolean }).standalone === true
    return window.matchMedia('(display-mode: standalone)').matches || isIosStandalone
  }

  /**
   * Whether the user explicitly turned notifications off on this device.
   *
   * @returns True if disabled locally.
   */
  static isDisabledLocally(): boolean {
    return import.meta.client && window.localStorage.getItem(PUSH_DISABLED_STORAGE_KEY) === '1'
  }

  /**
   * Whether an active push subscription exists (permission granted and subscription present).
   *
   * @returns True if subscribed.
   */
  static async isSubscribed(): Promise<boolean> {
    if (!this.isSupported() || Notification.permission !== 'granted') {
      return false
    }
    const registration: ServiceWorkerRegistration | undefined = await navigator.serviceWorker.getRegistration()
    const subscription: PushSubscription | null = registration ? await registration.pushManager.getSubscription() : null
    return subscription !== null
  }

  /**
   * Register the service worker, subscribe to push and save the subscription server-side.
   * Assumes the notification permission is already granted.
   *
   * @returns True on success, false when push is unsupported or not configured on the server.
   */
  static async subscribe(): Promise<boolean> {
    if (!this.isSupported()) {
      return false
    }
    const vapid: VapidKeyResponse = await NotificationsService.getVapidKey()
    if (!vapid.configured || !vapid.public_key) {
      return false
    }
    const registration: ServiceWorkerRegistration = await navigator.serviceWorker.register('/sw.js')
    await navigator.serviceWorker.ready
    let subscription: PushSubscription | null = await registration.pushManager.getSubscription()
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.decodeApplicationServerKey(vapid.public_key),
      })
    }
    const subscriptionJson: PushSubscriptionJSON = subscription.toJSON()
    if (!subscriptionJson.endpoint || !subscriptionJson.keys?.p256dh || !subscriptionJson.keys?.auth) {
      return false
    }
    await NotificationsService.subscribe({
      endpoint: subscriptionJson.endpoint,
      keys: { p256dh: subscriptionJson.keys.p256dh, auth: subscriptionJson.keys.auth },
      user_agent: navigator.userAgent.slice(0, 400),
    })
    this.rememberDisabled(false)
    return true
  }

  /**
   * Unsubscribe this device and remember the choice, so the auto-subscribe plugin leaves it off.
   */
  static async unsubscribe(): Promise<void> {
    this.rememberDisabled(true)
    if (!this.isSupported()) {
      return
    }
    const registration: ServiceWorkerRegistration | undefined = await navigator.serviceWorker.getRegistration()
    const subscription: PushSubscription | null = registration ? await registration.pushManager.getSubscription() : null
    if (subscription) {
      await NotificationsService.unsubscribe(subscription.endpoint).catch((): void => {})
      await subscription.unsubscribe()
    }
  }

  /**
   * Persist the user's on/off choice so auto-subscribe respects it.
   *
   * @param isDisabled - Whether notifications are turned off on this device.
   */
  private static rememberDisabled(isDisabled: boolean): void {
    if (!import.meta.client) {
      return
    }
    if (isDisabled) {
      window.localStorage.setItem(PUSH_DISABLED_STORAGE_KEY, '1')
    } else {
      window.localStorage.removeItem(PUSH_DISABLED_STORAGE_KEY)
    }
  }

  /**
   * Decode a base64url VAPID key into the bytes the Push API expects.
   *
   * @param base64UrlKey - The base64url application-server key.
   * @returns The decoded bytes.
   */
  private static decodeApplicationServerKey(base64UrlKey: string): Uint8Array<ArrayBuffer> {
    const padding: string = '='.repeat((4 - (base64UrlKey.length % 4)) % 4)
    const base64Key: string = (base64UrlKey + padding).replace(/-/g, '+').replace(/_/g, '/')
    const rawKey: string = atob(base64Key)
    const keyBytes: Uint8Array<ArrayBuffer> = new Uint8Array(rawKey.length)
    for (let index: number = 0; index < rawKey.length; index += 1) {
      keyBytes[index] = rawKey.charCodeAt(index)
    }
    return keyBytes
  }
}
