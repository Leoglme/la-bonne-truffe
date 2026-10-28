<template>
  <UModal
    :open="desktopUpdateStore.isModalOpen"
    :dismissible="desktopUpdateStore.canDismiss"
    :close="desktopUpdateStore.canDismiss"
    :title="DESKTOP_UPDATE_TITLES[desktopUpdateStore.status]"
    :description="DESKTOP_UPDATE_DESCRIPTIONS[desktopUpdateStore.status]"
    @update:open="onOpenChange"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <div
          v-if="desktopUpdateStore.currentVersion && desktopUpdateStore.nextVersion"
          class="flex items-center gap-2 text-sm font-extrabold"
        >
          <span class="rounded-full bg-chip px-3 py-1 text-ink-secondary"
            >v{{ desktopUpdateStore.currentVersion }}</span
          >
          <UIcon name="i-lucide-arrow-right" class="size-4 text-ink-label" />
          <span class="rounded-full bg-coral-pastel px-3 py-1 text-coral-text"
            >v{{ desktopUpdateStore.nextVersion }}</span
          >
        </div>
        <div v-if="desktopUpdateStore.status === 'downloading'" class="flex flex-col gap-2">
          <div class="flex items-center justify-between gap-3 text-sm text-ink-secondary">
            <span class="font-extrabold text-ink tabular-nums">{{ downloadLabel }}</span>
            <span v-if="desktopUpdateStore.totalBytes !== null" class="tabular-nums">
              {{ formatMegabytes(desktopUpdateStore.downloadedBytes) }} /
              {{ formatMegabytes(desktopUpdateStore.totalBytes) }} Mo
            </span>
          </div>
          <UProgress :model-value="desktopUpdateStore.downloadPercent" />
        </div>
        <p
          v-if="desktopUpdateStore.status === 'error' && desktopUpdateStore.errorMessage"
          role="alert"
          class="m-0 text-[15px] font-bold text-coral-text"
        >
          {{ desktopUpdateStore.errorMessage }}
        </p>
      </div>
    </template>
    <template #footer>
      <div class="flex w-full flex-wrap justify-end gap-3">
        <UButton
          v-if="desktopUpdateStore.canDismiss"
          color="neutral"
          variant="outline"
          size="xl"
          @click="desktopUpdateStore.dismiss()"
        >
          Plus tard
        </UButton>
        <UButton v-if="desktopUpdateStore.status === 'available'" size="xl" @click="desktopUpdateStore.installUpdate()">
          Installer la mise à jour
        </UButton>
        <UButton v-if="desktopUpdateStore.status === 'error'" size="xl" @click="desktopUpdateStore.installUpdate()">
          Réessayer
        </UButton>
        <UButton
          v-if="desktopUpdateStore.status === 'installed'"
          size="xl"
          loading-auto
          @click="desktopUpdateStore.restartApp()"
        >
          Redémarrer l’application
        </UButton>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import { computed } from 'vue'
import { DESKTOP_UPDATE_DESCRIPTIONS, DESKTOP_UPDATE_TITLES } from '~/constants/desktopUpdate'

const desktopUpdateStore: ReturnType<typeof useDesktopUpdateStore> = useDesktopUpdateStore()

const BYTES_PER_MEGABYTE: number = 1024 * 1024
const MEGABYTE_FORMAT: Intl.NumberFormat = new Intl.NumberFormat('fr-FR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

const downloadLabel: ComputedRef<string> = computed((): string => {
  if (desktopUpdateStore.downloadPercent !== null) {
    return `${desktopUpdateStore.downloadPercent} %`
  }
  if (desktopUpdateStore.downloadedBytes > 0) {
    return `${formatMegabytes(desktopUpdateStore.downloadedBytes)} Mo téléchargés`
  }
  return 'Préparation du téléchargement…'
})

/**
 * Close the modal when the user dismisses it, if the update can wait.
 *
 * @param isOpen - New open state.
 */
function onOpenChange(isOpen: boolean): void {
  if (!isOpen) {
    desktopUpdateStore.dismiss()
  }
}

/**
 * Write a size in megabytes, with one French decimal.
 *
 * @param bytes - The size in bytes.
 * @returns « 3,2 ».
 */
function formatMegabytes(bytes: number): string {
  return MEGABYTE_FORMAT.format(bytes / BYTES_PER_MEGABYTE)
}
</script>
