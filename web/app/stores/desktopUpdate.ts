import type { DownloadEvent, Update } from '@tauri-apps/plugin-updater'
import type { ComputedRef, Ref, ShallowRef } from 'vue'
import type { DesktopUpdateStatus } from '~/types/DesktopUpdate'
import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'

const UPDATE_CHECKED_STORAGE_KEY: string = 'lbt-update-checked'

/** Pinia store of the desktop app update: the check at startup, the download and its progress, the restart. */
export const useDesktopUpdateStore = defineStore('desktopUpdate', () => {
  const status: Ref<DesktopUpdateStatus> = ref('idle')
  const isModalOpen: Ref<boolean> = ref(false)
  const currentVersion: Ref<string | null> = ref(null)
  const nextVersion: Ref<string | null> = ref(null)
  const downloadedBytes: Ref<number> = ref(0)
  const totalBytes: Ref<number | null> = ref(null)
  const errorMessage: Ref<string | null> = ref(null)
  const pendingUpdate: ShallowRef<Update | null> = shallowRef(null)

  const downloadPercent: ComputedRef<number | null> = computed((): number | null => {
    if (totalBytes.value === null) {
      return null
    }
    return Math.min(100, Math.round((100 * downloadedBytes.value) / totalBytes.value))
  })
  const canDismiss: ComputedRef<boolean> = computed(
    (): boolean => status.value === 'available' || status.value === 'error',
  )

  /**
   * Look for a newer release once per session, and open the modal when there is one.
   */
  async function checkForUpdate(): Promise<void> {
    if (sessionStorage.getItem(UPDATE_CHECKED_STORAGE_KEY) === '1') {
      return
    }
    sessionStorage.setItem(UPDATE_CHECKED_STORAGE_KEY, '1')
    const { check }: typeof import('@tauri-apps/plugin-updater') = await import('@tauri-apps/plugin-updater')
    const update: Update | null = await check()

    if (update === null) {
      return
    }
    pendingUpdate.value = update
    currentVersion.value = update.currentVersion
    nextVersion.value = update.version
    status.value = 'available'
    isModalOpen.value = true
  }

  /**
   * Download and install the release found by the check, following the progress of the download.
   */
  async function installUpdate(): Promise<void> {
    if (pendingUpdate.value === null) {
      return
    }
    status.value = 'downloading'
    errorMessage.value = null
    downloadedBytes.value = 0
    totalBytes.value = null
    try {
      await pendingUpdate.value.downloadAndInstall(trackDownload)
      status.value = 'installed'
    } catch (error: unknown) {
      status.value = 'error'
      errorMessage.value = error instanceof Error ? error.message : String(error)
    }
  }

  /**
   * Restart the app on the installed version.
   */
  async function restartApp(): Promise<void> {
    const { relaunch }: typeof import('@tauri-apps/plugin-process') = await import('@tauri-apps/plugin-process')
    await relaunch()
  }

  /**
   * Close the modal, when the update can wait.
   */
  function dismiss(): void {
    if (canDismiss.value) {
      isModalOpen.value = false
    }
  }

  /**
   * Count the bytes downloaded so far, from the events the updater sends while downloading.
   *
   * @param event - Event of the download.
   */
  function trackDownload(event: DownloadEvent): void {
    if (event.event === 'Started') {
      const contentLength: number = event.data.contentLength ?? 0
      totalBytes.value = contentLength > 0 ? contentLength : null
      return
    }
    if (event.event === 'Progress') {
      downloadedBytes.value += event.data.chunkLength
    }
  }

  return {
    status,
    isModalOpen,
    currentVersion,
    nextVersion,
    downloadedBytes,
    totalBytes,
    errorMessage,
    downloadPercent,
    canDismiss,
    checkForUpdate,
    installUpdate,
    restartApp,
    dismiss,
  }
})
