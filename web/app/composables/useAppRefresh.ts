import type { Router } from 'vue-router'
import type { UseAppRefreshReturn } from '~/types/Composables'

/** Reloads what the screens show once news reached the device: a push, or a resume after a while away. */
export function useAppRefresh(): UseAppRefreshReturn {
  const router: Router = useRouter()
  const userStore: ReturnType<typeof useUserStore> = useUserStore()
  const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
  const bellStore: ReturnType<typeof useBellStore> = useBellStore()
  const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()
  const sourcesStore: ReturnType<typeof useSourcesStore> = useSourcesStore()

  /**
   * Reload the litters, the bell, the follow-ups, the sources and the litter shown; a signed-out device reloads nothing.
   */
  async function refreshAfterNews(): Promise<void> {
    if (!userStore.token) {
      return
    }
    const routeLitterId: unknown = router.currentRoute.value.params['id']
    const shownLitterId: number | null =
      typeof routeLitterId === 'string' ? Number(routeLitterId) : (littersStore.selectedLitter?.id ?? null)
    await Promise.all([
      littersStore.load(),
      bellStore.load(),
      followUpsStore.load(),
      sourcesStore.load(),
      shownLitterId === null ? Promise.resolve() : littersStore.select(shownLitterId).catch((): void => undefined),
    ])
  }

  /**
   * Count the resume as a new launch (the « Nouveau » badges move), then reload everything.
   */
  async function refreshAfterResume(): Promise<void> {
    if (!userStore.token) {
      return
    }
    await littersStore.recordResumeVisit()
    await refreshAfterNews()
  }

  return { refreshAfterNews, refreshAfterResume }
}
