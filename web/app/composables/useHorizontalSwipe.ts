import type { ComputedRef, CSSProperties, Ref } from 'vue'
import type {
  HorizontalSwipeDirection,
  HorizontalSwipeGestureAxis,
  HorizontalSwipeOptions,
  UseHorizontalSwipeReturn,
} from '~/types/Composables'
import { computed, nextTick, ref } from 'vue'

const AXIS_LOCK_DISTANCE_IN_PIXELS: number = 10
const SCREEN_EDGE_WIDTH_IN_PIXELS: number = 20
const COMMIT_DISTANCE_SCREEN_RATIO: number = 0.25
const FLICK_MINIMUM_DISTANCE_IN_PIXELS: number = 40
const FLICK_MINIMUM_SPEED_IN_PIXELS_PER_MILLISECOND: number = 0.5
const MISSING_NEIGHBOR_RESISTANCE: number = 0.3
const SLIDE_DURATION_IN_MILLISECONDS: number = 220

/**
 * Wait for a number of milliseconds.
 *
 * @param durationInMilliseconds - How long to wait.
 * @returns A promise resolved once the time has passed.
 */
function wait(durationInMilliseconds: number): Promise<void> {
  return new Promise((resolve: () => void): void => {
    setTimeout(resolve, durationInMilliseconds)
  })
}

/**
 * Write the pending styles to the page, so that the next style change starts a transition from them.
 */
async function commitPendingStyles(): Promise<void> {
  await nextTick()
  document.body.getBoundingClientRect()
}

/**
 * Tell which neighbour a horizontal move points to: moving the finger left shows the next one.
 *
 * @param deltaXInPixels - Horizontal move of the finger since the touch started.
 * @returns The direction of the neighbour.
 */
function resolveDirection(deltaXInPixels: number): HorizontalSwipeDirection {
  return deltaXInPixels < 0 ? 'next' : 'previous'
}

/**
 * Let a content follow a horizontal swipe, then slide it out and slide its neighbour in; vertical moves keep scrolling.
 *
 * @param options - Whether a neighbour exists in a direction, and how to show it.
 * @returns The style of the swiped element and its touch handlers.
 */
export function useHorizontalSwipe(options: HorizontalSwipeOptions): UseHorizontalSwipeReturn {
  const offsetInPixels: Ref<number> = ref(0)
  const isTransitionEnabled: Ref<boolean> = ref(true)

  let gestureAxis: HorizontalSwipeGestureAxis = 'ignored'
  let isSliding: boolean = false
  let startX: number = 0
  let startY: number = 0
  let startTimeStamp: number = 0
  let deltaX: number = 0

  const swipeStyle: ComputedRef<CSSProperties> = computed((): CSSProperties => ({
    transform: offsetInPixels.value === 0 ? undefined : `translateX(${offsetInPixels.value}px)`,
    transition: isTransitionEnabled.value ? `transform ${SLIDE_DURATION_IN_MILLISECONDS}ms ease-out` : 'none',
  }))

  /**
   * Start following a one-finger touch, unless it starts on a screen edge, where the browser swipes back.
   *
   * @param event - The touch start.
   */
  function onTouchStart(event: TouchEvent): void {
    const touch: Touch | undefined = event.touches[0]
    const isOnScreenEdge: boolean =
      touch !== undefined &&
      (touch.clientX < SCREEN_EDGE_WIDTH_IN_PIXELS || touch.clientX > window.innerWidth - SCREEN_EDGE_WIDTH_IN_PIXELS)

    if (isSliding || event.touches.length !== 1 || touch === undefined || isOnScreenEdge) {
      gestureAxis = 'ignored'
      return
    }
    gestureAxis = 'undecided'
    startX = touch.clientX
    startY = touch.clientY
    startTimeStamp = event.timeStamp
    deltaX = 0
  }

  /**
   * Decide on the first moves whether the touch swipes or scrolls, then move the content with the finger.
   *
   * @param event - The touch move.
   */
  function onTouchMove(event: TouchEvent): void {
    const touch: Touch | undefined = event.touches[0]
    if (touch === undefined || gestureAxis === 'ignored' || gestureAxis === 'vertical') {
      return
    }
    const moveX: number = touch.clientX - startX
    const moveY: number = touch.clientY - startY

    if (gestureAxis === 'undecided') {
      if (Math.abs(moveX) < AXIS_LOCK_DISTANCE_IN_PIXELS && Math.abs(moveY) < AXIS_LOCK_DISTANCE_IN_PIXELS) {
        return
      }
      gestureAxis = Math.abs(moveX) > Math.abs(moveY) ? 'horizontal' : 'vertical'
      if (gestureAxis === 'vertical') {
        return
      }
      isTransitionEnabled.value = false
    }
    deltaX = moveX
    offsetInPixels.value = options.canSwipeTo(resolveDirection(moveX)) ? moveX : moveX * MISSING_NEIGHBOR_RESISTANCE
  }

  /**
   * Show the neighbour when the swipe went far or fast enough, otherwise spring back.
   *
   * @param event - The touch end.
   */
  async function onTouchEnd(event: TouchEvent): Promise<void> {
    if (gestureAxis !== 'horizontal') {
      gestureAxis = 'ignored'
      return
    }
    gestureAxis = 'ignored'
    isTransitionEnabled.value = true

    const direction: HorizontalSwipeDirection = resolveDirection(deltaX)
    const distance: number = Math.abs(deltaX)
    const speed: number = distance / Math.max(1, event.timeStamp - startTimeStamp)
    const isFarEnough: boolean = distance > window.innerWidth * COMMIT_DISTANCE_SCREEN_RATIO
    const isFlick: boolean =
      distance > FLICK_MINIMUM_DISTANCE_IN_PIXELS && speed > FLICK_MINIMUM_SPEED_IN_PIXELS_PER_MILLISECOND

    if (!options.canSwipeTo(direction) || (!isFarEnough && !isFlick)) {
      offsetInPixels.value = 0
      return
    }
    await slideToNeighbor(direction)
  }

  /**
   * Spring back when the system takes the touch over.
   */
  function onTouchCancel(): void {
    gestureAxis = 'ignored'
    isTransitionEnabled.value = true
    offsetInPixels.value = 0
  }

  /**
   * Slide the content out on the side of the swipe, swap it, then slide the new one in from the other side.
   *
   * @param direction - The neighbour to show.
   */
  async function slideToNeighbor(direction: HorizontalSwipeDirection): Promise<void> {
    const screenWidth: number = window.innerWidth
    const exitSide: number = direction === 'next' ? -1 : 1
    isSliding = true
    try {
      offsetInPixels.value = exitSide * screenWidth
      await wait(SLIDE_DURATION_IN_MILLISECONDS)
      await options.showNeighbor(direction)

      isTransitionEnabled.value = false
      offsetInPixels.value = -exitSide * screenWidth
      await commitPendingStyles()
      isTransitionEnabled.value = true
      offsetInPixels.value = 0
      await wait(SLIDE_DURATION_IN_MILLISECONDS)
    } finally {
      isTransitionEnabled.value = true
      offsetInPixels.value = 0
      isSliding = false
    }
  }

  return { swipeStyle, onTouchStart, onTouchMove, onTouchEnd, onTouchCancel }
}
