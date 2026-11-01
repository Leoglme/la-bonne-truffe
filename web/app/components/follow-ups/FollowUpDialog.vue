<template>
  <UiDialog
    :open="litter !== null"
    :title="litter?.name ?? ''"
    description="Où en est l’échange"
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
        v-if="litter && litter.follow_up"
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

        <div :class="isShownAsWindow ? 'flex flex-col gap-6' : 'contents'">
          <div class="flex flex-col gap-2">
            <label :for="statusFieldId" class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">
              Statut
            </label>
            <div class="relative">
              <select
                :id="statusFieldId"
                :value="selectedStatus"
                :disabled="followUpsStore.isSaving"
                class="min-h-[52px] w-full appearance-none rounded-2xl border-2 border-line-strong bg-card ps-4 pe-12 text-[17px] font-bold text-ink disabled:opacity-60"
                @change="changeStatus"
              >
                <option v-for="option in FOLLOW_UP_STATUS_OPTIONS" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <UIcon
                name="i-lucide-chevrons-up-down"
                class="pointer-events-none absolute end-4 top-1/2 size-5 -translate-y-1/2 text-ink-muted"
              />
            </div>
            <span v-if="lastContactLabel" class="text-sm text-ink-muted">{{ lastContactLabel }}</span>
          </div>

          <FollowUpFoundPuppyCard
            v-if="isFoundPuppyCardShown"
            :litter="litter"
            @confirmed="followUpsStore.close()"
            @dismissed="isFoundPuppyCardDismissed = true"
          />

          <FollowUpReminderField
            :model-value="litter.follow_up.next_reminder_at ?? null"
            :is-disabled="followUpsStore.isSaving"
            @update:model-value="saveReminder"
          />

          <FollowUpStopButton
            :key="`stop-${litter.id}`"
            label="Ne plus suivre cette portée"
            :question="`Ne plus suivre ${litter.name} ?`"
            consequence="Son statut, son rappel et tes notes seront effacés."
            :stop-action="stopFollowing"
            :class="isShownAsWindow ? '' : 'order-last'"
          />
        </div>

        <FollowUpNotesSection
          :key="litter.id"
          :notes="litter.follow_up.notes"
          :add-note="addNote"
          :remove-note="removeNote"
        />
      </div>
    </template>
  </UiDialog>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { FollowUpStatus, LitterDetail, LitterFollowUp } from '~/types/api'
import { computed, ref, useId, watch } from 'vue'
import { FOLLOW_UP_STATUS_OPTIONS } from '~/constants/followUpOptions'
import { ChoiceValues } from '~/utils/choiceValues'
import { FollowUpPresentation } from '~/utils/followUpPresentation'

const route: RouteLocationNormalizedLoaded = useRoute()
const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()
const puppyArrivalStore: ReturnType<typeof usePuppyArrivalStore> = usePuppyArrivalStore()

const statusFieldId: string = useId()

const isFoundPuppyCardDismissed: Ref<boolean> = ref(false)
const actionError: Ref<string | null> = ref(null)

const litter: ComputedRef<LitterDetail | null> = computed((): LitterDetail | null => followUpsStore.openedLitter)
const selectedStatus: ComputedRef<FollowUpStatus | null> = computed((): FollowUpStatus | null => {
  const status: FollowUpStatus | undefined = litter.value?.follow_up?.status
  if (status === undefined) {
    return null
  }
  return status === 'new' ? 'to_contact' : status
})
const isFoundPuppyCardShown: ComputedRef<boolean> = computed(
  (): boolean =>
    selectedStatus.value === 'reserved' && !puppyArrivalStore.isSearchPaused && !isFoundPuppyCardDismissed.value,
)
const lastContactLabel: ComputedRef<string | null> = computed((): string | null =>
  FollowUpPresentation.buildLastContactLabel(litter.value?.follow_up?.last_contact_at ?? null),
)

/**
 * Close the dialog when the user dismisses it.
 *
 * @param isOpen - New open state.
 */
function onOpenChange(isOpen: boolean): void {
  if (!isOpen) {
    followUpsStore.close()
  }
}

/**
 * Run a change of the follow-up; when it fails, show why in red.
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
 * Save the status picked in the list, keeping the reminder.
 *
 * @param event - Change of the status list.
 */
async function changeStatus(event: Event): Promise<void> {
  const select: EventTarget | null = event.target
  const followUp: LitterFollowUp | null | undefined = litter.value?.follow_up
  if (!(select instanceof HTMLSelectElement) || !ChoiceValues.isFollowUpStatus(select.value) || !followUp) {
    return
  }
  const status: FollowUpStatus = select.value
  await tryChange((): Promise<void> =>
    followUpsStore.saveFollowUp({
      status,
      next_reminder_at: followUp.next_reminder_at,
      last_contact_at: status === 'contacted' ? new Date().toISOString() : followUp.last_contact_at,
    }),
  )
}

/**
 * Save the reminder picked, keeping the status, or remove it.
 *
 * @param nextReminderAt - The reminder time, as an ISO string, or null to remove it.
 */
async function saveReminder(nextReminderAt: string | null): Promise<void> {
  const followUp: LitterFollowUp | null | undefined = litter.value?.follow_up
  if (!followUp) {
    return
  }
  await tryChange((): Promise<void> =>
    followUpsStore.saveFollowUp({
      status: followUp.status,
      next_reminder_at: nextReminderAt,
      last_contact_at: followUp.last_contact_at,
    }),
  )
}

/**
 * Add a note to the follow-up.
 *
 * @param text - The note.
 */
async function addNote(text: string): Promise<void> {
  await tryChange((): Promise<void> => followUpsStore.addNote(text))
}

/**
 * Delete a note of the follow-up.
 *
 * @param noteId - The note.
 */
async function removeNote(noteId: number): Promise<void> {
  await tryChange((): Promise<void> => followUpsStore.removeNote(noteId))
}

/**
 * Stop following the litter once confirmed; the dialog closes.
 */
async function stopFollowing(): Promise<void> {
  await tryChange((): Promise<void> => followUpsStore.stopFollowing())
}

watch(
  (): string => route.fullPath,
  (): void => followUpsStore.close(),
)

watch(
  (): number | undefined => litter.value?.id,
  (): void => {
    isFoundPuppyCardDismissed.value = false
    actionError.value = null
  },
)
</script>
