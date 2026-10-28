import { watch } from 'vue'
import { WebPush } from '~/utils/webPush'

/**
 * Auto-subscribe to Web Push once the permission is granted, so notifications stay on by default,
 * unless the user turned them off on this device. The first permission still needs the settings
 * switch (an iOS user-gesture requirement). Inactive in the Tauri build. Copied from DevLeadHunter.
 */
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
    await WebPush.subscribe().catch((): boolean => false)
  }

  void ensureSubscribed()
  watch(
    (): string | null => userStore.token,
    (): void => {
      void ensureSubscribed()
    },
  )
})
