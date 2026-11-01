<template>
  <UiDialog
    :open="breeder !== null"
    :title="dialogTitle"
    description="Tu seras prévenu de ce qui se passe chez eux, même en dehors de tes départements."
    is-wide-window
    :drawer-ui="{
      content: 'rounded-t-3xl bg-card md:mx-auto md:w-full md:max-w-2xl',
      container: 'gap-5 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="onOpenChange"
  >
    <template #body="{ isShownAsWindow }">
      <div
        v-if="breeder"
        :class="isShownAsWindow ? 'grid grid-cols-2 items-start gap-x-10 gap-y-6' : 'flex flex-col gap-6'"
      >
        <p
          v-if="actionError"
          role="alert"
          class="m-0 text-[15px] font-bold text-coral-text"
          :class="isShownAsWindow ? 'col-span-2' : ''"
        >
          {{ actionError }}
        </p>

        <div class="flex flex-col gap-2.5">
          <div
            v-for="setting in BREEDER_NOTIFICATION_SETTINGS"
            :key="setting.key"
            class="flex items-center justify-between gap-3 rounded-[20px] bg-cream px-4 py-3.5"
          >
            <span class="flex min-w-0 flex-col">
              <span class="text-[17px] font-bold">{{ setting.label }}</span>
              <span class="text-sm text-ink-muted">{{ setting.helper }}</span>
            </span>
            <USwitch
              :model-value="draft[setting.key]"
              :aria-label="setting.label"
              :disabled="breederFollowStore.isSaving"
              @update:model-value="(isOn: boolean): void => setSetting(setting.key, isOn)"
            />
          </div>
        </div>

        <div :class="isShownAsWindow ? 'flex flex-col gap-6' : 'contents'">
          <div class="flex flex-col gap-2">
            <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Dans mon carnet</span>
            <div role="group" aria-label="Statut de l’éleveur dans mon carnet" class="flex flex-wrap gap-2">
              <button
                v-for="option in BREEDER_FOLLOW_STATUS_OPTIONS"
                :key="option.value"
                type="button"
                :aria-pressed="draft.status === option.value"
                :disabled="breederFollowStore.isSaving"
                class="min-h-11 rounded-full px-[18px] text-[15px] font-extrabold whitespace-nowrap shadow-chip"
                :class="draft.status === option.value ? 'bg-ink text-cream' : 'bg-card text-ink-secondary'"
                @click="draft.status = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <FollowUpReminderField v-model="draft.next_reminder_at" :is-disabled="breederFollowStore.isSaving" />

          <div class="flex flex-col gap-2.5">
            <UButton
              size="xl"
              class="min-h-[56px] w-full justify-center gap-2 text-[17px]"
              :loading="breederFollowStore.isSaving"
              @click="saveFollow"
            >
              <template v-if="breeder.follow === null" #leading>
                <UiCustomIcon name="heart" :size-in-pixels="20" :stroke-width="2.2" />
              </template>
              {{ breeder.follow === null ? 'Suivre cet élevage' : 'Enregistrer' }}
            </UButton>
            <UButton
              color="neutral"
              variant="outline"
              size="xl"
              class="min-h-[52px] w-full justify-center text-[17px]"
              :disabled="breederFollowStore.isSaving"
              @click="breederFollowStore.close()"
            >
              Annuler
            </UButton>
          </div>
        </div>

        <template v-if="breeder.follow">
          <FollowUpNotesSection
            :key="breeder.id"
            :notes="breeder.follow.notes"
            placeholder="Appel du jour, liste d’attente, lice qui va être saillie…"
            :add-note="addNote"
            :remove-note="removeNote"
            class="border-t border-line pt-5"
            :class="isShownAsWindow ? 'col-span-2' : ''"
          />
          <FollowUpStopButton
            :key="`stop-${breeder.id}`"
            label="Ne plus suivre cet élevage"
            :question="`Ne plus suivre ${breeder.name} ?`"
            consequence="Ses alertes, son statut, son rappel et tes notes seront effacés."
            :stop-action="stopFollowing"
            :class="isShownAsWindow ? 'col-span-2' : ''"
          />
        </template>
      </div>
    </template>
  </UiDialog>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { BreederDetail, BreederFollow, BreederFollowUpdate } from '~/types/api'
import type { BreederNotificationSettingKey } from '~/types/Breeder'
import { computed, ref, watch } from 'vue'
import {
  BREEDER_FOLLOW_STATUS_OPTIONS,
  BREEDER_NOTIFICATION_SETTINGS,
  DEFAULT_BREEDER_FOLLOW,
} from '~/constants/breederOptions'

const route: RouteLocationNormalizedLoaded = useRoute()
const breederFollowStore: ReturnType<typeof useBreederFollowStore> = useBreederFollowStore()

const draft: Ref<BreederFollowUpdate> = ref({ ...DEFAULT_BREEDER_FOLLOW })
const actionError: Ref<string | null> = ref(null)

const breeder: ComputedRef<BreederDetail | null> = computed(
  (): BreederDetail | null => breederFollowStore.openedBreeder,
)
const dialogTitle: ComputedRef<string> = computed((): string => buildDialogTitle())

/**
 * Title the dialog: « Suivre … » for a first follow, the name of the breeding once followed.
 *
 * @returns The title, empty while the dialog is closed.
 */
function buildDialogTitle(): string {
  if (breeder.value === null) {
    return ''
  }
  if (breeder.value.follow === null) {
    return `Suivre ${breeder.value.name}`
  }
  return breeder.value.name
}

/**
 * Start the draft from the follow of the breeder opened, or from the defaults for a first follow.
 */
function resetDraft(): void {
  const follow: BreederFollow | null = breeder.value?.follow ?? null
  draft.value =
    follow === null
      ? { ...DEFAULT_BREEDER_FOLLOW }
      : {
          status: follow.status,
          notify_new_mating: follow.notify_new_mating,
          notify_birth: follow.notify_birth,
          notify_new_photos: follow.notify_new_photos,
          notify_ignored_colors: follow.notify_ignored_colors,
          next_reminder_at: follow.next_reminder_at,
          last_contact_at: follow.last_contact_at,
        }
  actionError.value = null
}

/**
 * Close the dialog when the user dismisses it.
 *
 * @param isOpen - New open state.
 */
function onOpenChange(isOpen: boolean): void {
  if (!isOpen) {
    breederFollowStore.close()
  }
}

/**
 * Run a change of the follow; when it fails, show why in red.
 *
 * @param change - The call to the store.
 */
async function tryChange(change: () => Promise<void>): Promise<void> {
  actionError.value = null
  try {
    await change()
  } catch (error: unknown) {
    actionError.value = error instanceof Error ? error.message : 'Enregistrement impossible'
  }
}

/**
 * Turn an alert of the draft on or off.
 *
 * @param key - The alert.
 * @param isOn - Its new state.
 */
function setSetting(key: BreederNotificationSettingKey, isOn: boolean): void {
  draft.value = { ...draft.value, [key]: isOn }
}

/**
 * Save the draft: the first follow of the breeder, or its alerts, status and reminder changed; then close.
 */
async function saveFollow(): Promise<void> {
  const hasJustBeenContacted: boolean =
    draft.value.status === 'contacted' && breeder.value?.follow?.status !== 'contacted'
  await tryChange(async (): Promise<void> => {
    await breederFollowStore.saveFollow({
      ...draft.value,
      last_contact_at: hasJustBeenContacted ? new Date().toISOString() : draft.value.last_contact_at,
    })
    breederFollowStore.close()
  })
}

/**
 * Add a note to the follow.
 *
 * @param text - The note.
 */
async function addNote(text: string): Promise<void> {
  await tryChange((): Promise<void> => breederFollowStore.addNote(text))
}

/**
 * Delete a note of the follow.
 *
 * @param noteId - The note.
 */
async function removeNote(noteId: number): Promise<void> {
  await tryChange((): Promise<void> => breederFollowStore.removeNote(noteId))
}

/**
 * Stop following the breeder once confirmed; the dialog closes.
 */
async function stopFollowing(): Promise<void> {
  await tryChange((): Promise<void> => breederFollowStore.stopFollowing())
}

watch(
  (): string => route.fullPath,
  (): void => breederFollowStore.close(),
)

watch(
  (): number | undefined => breeder.value?.id,
  (): void => resetDraft(),
)
</script>
