import type { ComputedRef, Ref } from 'vue'
import type { TestNotificationResult } from '~/types/api'

export type WebPushError = 'permission' | 'not-configured' | 'unexpected'

export type UseDesktopRuntimeReturn = {
  isDesktopApp: ComputedRef<boolean>
  isProdDesktop: ComputedRef<boolean>
}

export type UseWebPushReturn = {
  isSupported: Ref<boolean>
  isStandalone: Ref<boolean>
  isSubscribed: Ref<boolean>
  isBusy: Ref<boolean>
  error: Ref<WebPushError | null>
  toggle: (shouldBeEnabled: boolean) => Promise<void>
  sendTest: () => Promise<TestNotificationResult>
}
