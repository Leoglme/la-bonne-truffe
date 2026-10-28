import type { ComputedRef } from 'vue'
import type { TauriWindow } from '~/types/Browser'
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
    return (window as TauriWindow).__TAURI_INTERNALS__ !== undefined
  })

  const isProdDesktop: ComputedRef<boolean> = computed((): boolean => isDesktopApp.value && !import.meta.dev)

  return { isDesktopApp, isProdDesktop }
}
