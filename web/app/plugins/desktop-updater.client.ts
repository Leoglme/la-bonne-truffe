import type { Update } from '@tauri-apps/plugin-updater'

/**
 * Packaged desktop app only: look for a newer release at startup and offer to install it.
 * The updater reads `latest.json` from the GitHub releases (see src-tauri/tauri.conf.json).
 */
export default defineNuxtPlugin((): void => {
  const { isProdDesktop }: ReturnType<typeof useDesktopRuntime> = useDesktopRuntime()
  if (!isProdDesktop.value) {
    return
  }
  const toast: ReturnType<typeof useToast> = useToast()

  /**
   * Download and install the update, then restart the app on the new version.
   *
   * @param update - The update found by the check.
   */
  async function installUpdate(update: Update): Promise<void> {
    await update.downloadAndInstall()
    const { relaunch }: typeof import('@tauri-apps/plugin-process') = await import('@tauri-apps/plugin-process')
    await relaunch()
  }

  /**
   * Check for an update and, when one exists, show a toast that installs it.
   */
  async function offerUpdate(): Promise<void> {
    const { check }: typeof import('@tauri-apps/plugin-updater') = await import('@tauri-apps/plugin-updater')
    const update: Update | null = await check()
    if (!update) {
      return
    }
    toast.add({
      title: `La version ${update.version} est disponible`,
      duration: 0,
      actions: [
        {
          label: 'Installer et redémarrer',
          onClick: (): void => {
            void installUpdate(update)
          },
        },
      ],
    })
  }

  void offerUpdate().catch((): void => {})
})
