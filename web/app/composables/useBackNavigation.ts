import type { Router } from 'vue-router'
import type { UseBackNavigationReturn } from '~/types/Composables'

/**
 * The « Retour » of a pushed screen: back to the screen it was opened from, or to a fallback when the app
 * started on it.
 *
 * @param fallbackPath - Where to go when there is no previous screen.
 * @returns The previous path, and the back action.
 */
export function useBackNavigation(fallbackPath: string): UseBackNavigationReturn {
  const router: Router = useRouter()

  /**
   * Read the path of the screen this one was opened from.
   *
   * @returns The path, or null when the app started here.
   */
  function readPreviousPath(): string | null {
    const previousPath: unknown = router.options.history.state['back']
    return typeof previousPath === 'string' ? previousPath : null
  }

  /**
   * Go back to the previous screen, or to the fallback when the app started here.
   */
  function goBack(): void {
    if (readPreviousPath() !== null) {
      router.back()
      return
    }
    navigateTo(fallbackPath)
  }

  return { readPreviousPath, goBack }
}
