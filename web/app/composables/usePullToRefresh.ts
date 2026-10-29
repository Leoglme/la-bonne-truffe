import type { ComputedRef, Ref } from 'vue'
import type { PullToRefreshGesture, UsePullToRefreshReturn } from '~/types/Composables'
import { computed, ref } from 'vue'
import { WebPush } from '~/utils/webPush'

const AXIS_LOCK_DISTANCE_IN_PIXELS: number = 10
const PULL_RESISTANCE: number = 0.5
const REFRESH_DISTANCE_IN_PIXELS: number = 72
const MAXIMUM_PULL_IN_PIXELS: number = 110

/**
 * Tell whether the screen under the finger is scrolled down, in which case pulling scrolls it back up.
 *
 * @param target - Element the touch started on.
 * @returns True when it, or one of its parents, is scrolled.
 */
function isScrolledUnder(target: EventTarget | null): boolean {
  let element: Element | null = target instanceof Element ? target : null
  while (element !== null) {
    if (element.scrollTop > 0) {
      return true
    }
    element = element.parentElement
  }
  return false
}

/**
 * Reload the installed app when a screen is pulled down from its top, as Safari does in a tab.
 *
 * @returns How far the screen is pulled, whether letting go reloads, and the touch handlers of the screen.
 */
export function usePullToRefresh(): UsePullToRefreshReturn {
  const pullDistanceInPixels: Ref<number> = ref(0)
  const isRefreshing: Ref<boolean> = ref(false)

  let gesture: PullToRefreshGesture = 'ignored'
  let startX: number = 0
  let startY: number = 0

  const isReadyToRefresh: ComputedRef<boolean> = computed(
    (): boolean => pullDistanceInPixels.value >= REFRESH_DISTANCE_IN_PIXELS,
  )

  /**
   * Start watching a one-finger touch in the installed app, when nothing under it is scrolled.
   *
   * @param event - The touch start.
   */
  function onTouchStart(event: TouchEvent): void {
    const touch: Touch | undefined = event.touches[0]
    if (
      isRefreshing.value ||
      event.touches.length !== 1 ||
      touch === undefined ||
      !WebPush.isStandalonePwa() ||
      isScrolledUnder(event.target)
    ) {
      gesture = 'ignored'
      return
    }
    gesture = 'undecided'
    startX = touch.clientX
    startY = touch.clientY
  }

  /**
   * Pull the indicator down with the finger, once the move goes down rather than sideways.
   *
   * @param event - The touch move.
   */
  function onTouchMove(event: TouchEvent): void {
    const touch: Touch | undefined = event.touches[0]
    if (touch === undefined || gesture === 'ignored') {
      return
    }
    const moveX: number = touch.clientX - startX
    const moveY: number = touch.clientY - startY

    if (gesture === 'undecided') {
      if (Math.abs(moveX) < AXIS_LOCK_DISTANCE_IN_PIXELS && Math.abs(moveY) < AXIS_LOCK_DISTANCE_IN_PIXELS) {
        return
      }
      gesture = moveY > Math.abs(moveX) ? 'pulling' : 'ignored'
    }
    if (gesture === 'pulling') {
      pullDistanceInPixels.value = Math.min(Math.max(0, moveY * PULL_RESISTANCE), MAXIMUM_PULL_IN_PIXELS)
    }
  }

  /**
   * Reload the app when the pull went far enough, otherwise put the indicator back.
   */
  function onTouchEnd(): void {
    if (gesture === 'pulling' && isReadyToRefresh.value) {
      isRefreshing.value = true
      pullDistanceInPixels.value = REFRESH_DISTANCE_IN_PIXELS
      window.location.reload()
      return
    }
    gesture = 'ignored'
    pullDistanceInPixels.value = 0
  }

  return { pullDistanceInPixels, isReadyToRefresh, isRefreshing, onTouchStart, onTouchMove, onTouchEnd }
}
