import type { Ref } from 'vue'
import type { TestNotificationResult } from '~/types/api'
import type { WebPushError } from '~/types/Composables'
import { onMounted, ref } from 'vue'
import { NotificationsService } from '~/services/notificationsService'
import { WebPush } from '~/utils/webPush'

/** Reactive state and actions behind the notifications switch. */
export type UseWebPush = {
  isSupported: Ref<boolean>
  isStandalone: Ref<boolean>
  isSubscribed: Ref<boolean>
  isBusy: Ref<boolean>
  error: Ref<WebPushError | null>
  toggle: (shouldBeEnabled: boolean) => Promise<void>
  sendTest: () => Promise<TestNotificationResult>
}

/**
 * Manage the push subscription of the current device (settings switch). Copied from DevLeadHunter.
 *
 * @returns Support flags, subscription state, and the toggle and test actions.
 */
export function useWebPush(): UseWebPush {
  const isSupported: Ref<boolean> = ref(false)
  const isStandalone: Ref<boolean> = ref(false)
  const isSubscribed: Ref<boolean> = ref(false)
  const isBusy: Ref<boolean> = ref(false)
  const error: Ref<WebPushError | null> = ref(null)

  /**
   * Read the current support and subscription state.
   */
  async function refresh(): Promise<void> {
    isSupported.value = WebPush.isSupported()
    isStandalone.value = WebPush.isStandalonePwa()
    isSubscribed.value = await WebPush.isSubscribed()
  }

  /**
   * Ask for the permission (the user gesture iOS requires) and subscribe.
   */
  async function enable(): Promise<void> {
    const permission: NotificationPermission = await Notification.requestPermission()
    if (permission !== 'granted') {
      error.value = 'permission'
      return
    }
    if (!(await WebPush.subscribe())) {
      error.value = 'not-configured'
      return
    }
    isSubscribed.value = true
  }

  /**
   * Turn notifications on or off on this device.
   *
   * @param shouldBeEnabled - Desired state of the switch.
   */
  async function toggle(shouldBeEnabled: boolean): Promise<void> {
    if (!isSupported.value || isBusy.value) {
      return
    }
    isBusy.value = true
    error.value = null
    try {
      if (shouldBeEnabled) {
        await enable()
      } else {
        await WebPush.unsubscribe()
        isSubscribed.value = false
      }
    } catch {
      error.value = 'unexpected'
    } finally {
      isBusy.value = false
    }
  }

  /**
   * Send a test notification to every device of the user.
   *
   * @returns The delivery diagnostic.
   */
  async function sendTest(): Promise<TestNotificationResult> {
    return NotificationsService.test()
  }

  onMounted((): void => {
    void refresh()
  })

  return { isSupported, isStandalone, isSubscribed, isBusy, error, toggle, sendTest }
}
