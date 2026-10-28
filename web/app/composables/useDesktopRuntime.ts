import type { ComputedRef } from 'vue'
import type { UseDesktopRuntimeReturn } from '~/types/Composables'
import { computed } from 'vue'

/**
 * Detect the runtime: Tauri desktop window or plain browser. Client-only, SSR-safe.
 *
 * @returns Whether the app runs in the Tauri window, and whether it is a packaged (non-dev) build.
 */
export function useDesktopRuntime(): UseDesktopRuntimeReturn {
  const isDesktopApp: ComputedRef<boolean> = computed((): boolean => {
    if (!import.meta.client) {
      return false
    }
    const tauriWindow: Window & { __TAURI_INTERNALS__?: unknown } = window as Window & {
      __TAURI_INTERNALS__?: unknown
    }
    return tauriWindow.__TAURI_INTERNALS__ !== undefined
  })

  // Dev has no valid updater endpoint: only a packaged app checks for updates.
  const isProdDesktop: ComputedRef<boolean> = computed((): boolean => isDesktopApp.value && !import.meta.dev)

  return { isDesktopApp, isProdDesktop }
}
