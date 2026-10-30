import type { UseAppRefreshReturn } from '~/types/Composables'

const RESUME_AFTER_HIDDEN_MS: number = 5 * 60_000

/** Reloads the screens when the app comes back after a while in the background: iOS keeps it as it was left. */
export default defineNuxtPlugin((): void => {
  const { refreshAfterResume }: UseAppRefreshReturn = useAppRefresh()
  let hiddenAt: number | null = null

  document.addEventListener('visibilitychange', (): void => {
    if (document.visibilityState === 'hidden') {
      hiddenAt = Date.now()
      return
    }
    if (hiddenAt !== null && Date.now() - hiddenAt >= RESUME_AFTER_HIDDEN_MS) {
      refreshAfterResume()
    }
    hiddenAt = null
  })
})
