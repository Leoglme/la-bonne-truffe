import { watch } from 'vue'
import { WebPush } from '~/utils/webPush'

/** Keeps the device subscribed to Web Push once the settings switch got the permission, unless turned off here. */
export default defineNuxtPlugin((): void => {
  const userStore: ReturnType<typeof useUserStore> = useUserStore()
  const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()

  /**
   * Make sure a fresh push subscription exists when the device is eligible.
   */
  async function ensureSubscribed(): Promise<void> {
    if (config.public.isDesktop || !WebPush.isSupported() || WebPush.isDisabledLocally()) {
      return
    }
    if (Notification.permission !== 'granted' || !userStore.token) {
      return
    }
    await WebPush.subscribe()
  }

  ensureSubscribed()
  watch(
    (): string | null => userStore.token,
    (): Promise<void> => ensureSubscribed(),
  )
})
