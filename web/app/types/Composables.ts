import type { ComputedRef } from 'vue'

/** Why turning push on failed: refused permission, no VAPID keys on the server, or anything else. */
export type WebPushError = 'permission' | 'not-configured' | 'unexpected'

export type UseDesktopRuntimeReturn = {
  isDesktopApp: ComputedRef<boolean>
  isProdDesktop: ComputedRef<boolean>
}
