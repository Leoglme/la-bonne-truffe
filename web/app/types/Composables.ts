import type { ComputedRef, CSSProperties, Ref } from 'vue'
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

export type HorizontalSwipeDirection = 'previous' | 'next'

export type HorizontalSwipeGestureAxis = 'undecided' | 'horizontal' | 'vertical' | 'ignored'

export type HorizontalSwipeOptions = {
  canSwipeTo: (direction: HorizontalSwipeDirection) => boolean
  showNeighbor: (direction: HorizontalSwipeDirection) => Promise<void>
}

export type UseHorizontalSwipeReturn = {
  swipeStyle: ComputedRef<CSSProperties>
  onTouchStart: (event: TouchEvent) => void
  onTouchMove: (event: TouchEvent) => void
  onTouchEnd: (event: TouchEvent) => Promise<void>
  onTouchCancel: () => void
}
