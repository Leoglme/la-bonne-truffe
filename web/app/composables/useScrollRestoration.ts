import type { Ref } from 'vue'
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router'
import type { UseScrollRestorationReturn } from '~/types/Composables'
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const SAVED_SCROLL_TOP_BY_SCREEN_PATH: Map<string, number> = new Map()

/**
 * Scroll a screen back to where the user left it, when they come back to it with « Retour ».
 *
 * @returns The ref to put on the element that scrolls the screen.
 */
export function useScrollRestoration(): UseScrollRestorationReturn {
  const route: RouteLocationNormalizedLoaded = useRoute()
  const router: Router = useRouter()
  const screenPath: string = route.path

  const scroller: Ref<HTMLElement | null> = ref(null)

  onMounted(async (): Promise<void> => {
    const hasUserComeBack: boolean = typeof router.options.history.state['forward'] === 'string'
    const savedScrollTop: number | undefined = SAVED_SCROLL_TOP_BY_SCREEN_PATH.get(screenPath)
    if (!hasUserComeBack || savedScrollTop === undefined) {
      return
    }
    await nextTick()
    scroller.value?.scrollTo({ top: savedScrollTop })
  })

  onBeforeUnmount((): void => {
    SAVED_SCROLL_TOP_BY_SCREEN_PATH.set(screenPath, scroller.value?.scrollTop ?? 0)
  })

  return { scroller }
}
