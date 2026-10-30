import { watch } from 'vue'

/** Asks the phone for its position once signed in, as a native app does, and refreshes it at each launch. */
export default defineNuxtPlugin((): void => {
  const userStore: ReturnType<typeof useUserStore> = useUserStore()
  const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()
  const { isDesktopApp }: ReturnType<typeof useDesktopRuntime> = useDesktopRuntime()

  locationStore.restore()
  if (isDesktopApp.value) {
    return
  }
  watch(
    (): string | null => userStore.token,
    (token: string | null): void => {
      if (token) {
        locationStore.refreshAtLaunch()
      }
    },
    { immediate: true },
  )
})
