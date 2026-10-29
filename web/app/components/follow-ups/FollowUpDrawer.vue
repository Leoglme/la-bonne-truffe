<template>
  <UDrawer
    :open="litter !== null"
    :title="litter?.name ?? ''"
    description="Où en est l’échange"
    :ui="{
      content: 'rounded-t-3xl bg-card md:mx-auto md:w-full md:max-w-2xl',
      container: 'gap-5 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="onOpenChange"
  >
    <template #body>
      <div v-if="litter && litter.follow_up" class="flex flex-col gap-6">
        <p v-if="actionError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">{{ actionError }}</p>

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
        </div>

        <div class="flex flex-col gap-2">
          <label :for="reminderFieldId" class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">
            Rappel
          </label>
          <div class="relative">
            <input
              :id="reminderFieldId"
              type="datetime-local"
              :value="reminderInputValue"
              :disabled="followUpsStore.isSaving"
              class="peer absolute inset-0 z-10 size-full cursor-pointer opacity-0 disabled:cursor-default"
              @click="openReminderPicker"
              @change="changeReminder"
            />
            <span
              class="flex min-h-[52px] items-center gap-3 rounded-2xl border-2 border-line-strong bg-card ps-4 pe-14 text-[17px] font-bold peer-focus-visible:outline-3 peer-focus-visible:outline-offset-3 peer-focus-visible:outline-coral peer-disabled:opacity-60"
              :class="reminderLabel ? 'text-ink' : 'text-ink-muted'"
            >
              <UIcon name="i-lucide-bell-ring" class="size-5 shrink-0 text-coral" />
              {{ reminderLabel ?? 'Choisir le jour et l’heure' }}
            </span>
            <button
              v-if="reminderLabel"
              type="button"
              aria-label="Retirer le rappel"
              :disabled="followUpsStore.isSaving"
              class="absolute end-1 top-1/2 z-20 inline-flex size-11 -translate-y-1/2 items-center justify-center rounded-full border-0 bg-transparent text-ink-muted"
              @click="clearReminder"
            >
              <UIcon name="i-lucide-x" class="size-5" />
            </button>
          </div>
          <span class="text-sm text-ink-muted">Une notification te prévient à cette heure-là.</span>
        </div>

        <div class="flex flex-col gap-2">
          <label :for="noteFieldId" class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">
            Nouvelle note
          </label>
          <textarea
            :id="noteFieldId"
            v-model="noteText"
            rows="3"
            placeholder="Appel du jour, liste d’attente, photos reçues…"
            class="rounded-2xl border-2 border-line-strong bg-card px-4 py-3 text-[17px] text-ink"
          />
          <UButton
            size="xl"
            class="mt-1 w-full justify-center md:w-auto md:self-start"
            :disabled="noteText.trim() === ''"
            loading-auto
            @click="addNote"
          >
            Ajouter la note
          </UButton>
        </div>

        <ul v-if="litter.follow_up.notes.length > 0" class="m-0 flex list-none flex-col gap-2.5 p-0">
          <li
            v-for="note in litter.follow_up.notes"
            :key="note.id"
            class="rounded-[14px] bg-cream py-2.5 ps-3.5 pe-1.5 text-[15px] leading-[1.45] text-ink-secondary"
          >
            <div class="flex items-start gap-2">
              <span class="min-w-0 grow">
                <span class="block text-[13px] font-extrabold text-ink-label">{{
                  formatNoteDay(note.created_at)
                }}</span>
                {{ note.text }}
              </span>
              <button
                v-if="noteIdAwaitingDeletion !== note.id"
                type="button"
                :aria-label="`Supprimer la note du ${formatNoteDay(note.created_at)}`"
                class="-mt-1 inline-flex size-11 shrink-0 items-center justify-center rounded-full border-0 bg-transparent text-ink-muted"
                @click="noteIdAwaitingDeletion = note.id"
              >
                <UIcon name="i-lucide-trash-2" class="size-5" />
              </button>
            </div>
            <div v-if="noteIdAwaitingDeletion === note.id" class="mt-2.5 flex flex-col gap-2.5 pe-2">
              <span class="font-bold text-ink">Supprimer cette note ?</span>
              <div class="flex gap-2">
                <UButton
                  color="neutral"
                  variant="outline"
                  class="flex-1 justify-center md:flex-none"
                  @click="noteIdAwaitingDeletion = null"
                >
                  Annuler
                </UButton>
                <UButton
                  loading-auto
                  class="min-h-12 flex-1 justify-center px-5 text-[15px] md:flex-none"
                  @click="removeNote(note.id)"
                >
                  Supprimer
                </UButton>
              </div>
            </div>
          </li>
        </ul>

        <div class="border-t border-line pt-4">
          <button
            v-if="!isStopFollowingConfirmShown"
            type="button"
            class="min-h-11 border-0 bg-transparent px-1 text-[15px] font-extrabold text-coral-text"
            @click="isStopFollowingConfirmShown = true"
          >
            Ne plus suivre cette portée
          </button>
          <div v-else class="flex flex-col gap-3 rounded-2xl bg-coral-pastel p-4">
            <p class="m-0 text-[15px] text-ink-secondary">
              <strong class="text-ink">Ne plus suivre {{ litter.name }} ?</strong>
              Son statut, son rappel et tes notes seront effacés.
            </p>
            <div class="flex gap-2">
              <UButton
                color="neutral"
                variant="outline"
                class="flex-1 justify-center md:flex-none"
                @click="isStopFollowingConfirmShown = false"
              >
                Annuler
              </UButton>
              <UButton
                loading-auto
                class="min-h-12 flex-1 justify-center px-5 text-[15px] md:flex-none"
                @click="stopFollowing"
              >
                Ne plus suivre
              </UButton>
            </div>
          </div>
        </div>
      </div>
    </template>
  </UDrawer>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { FollowUpStatus, LitterDetail, LitterFollowUp } from '~/types/api'
import { computed, ref, useId, watch } from 'vue'
import { FOLLOW_UP_STATUS_OPTIONS } from '~/constants/followUpOptions'
import { ChoiceValues } from '~/utils/choiceValues'
import { FrenchDate } from '~/utils/frenchDate'

const route: RouteLocationNormalizedLoaded = useRoute()
const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()

const FINE_POINTER_MEDIA_QUERY: string = '(pointer: fine)'

const statusFieldId: string = useId()
const reminderFieldId: string = useId()
const noteFieldId: string = useId()

const noteText: Ref<string> = ref('')
const noteIdAwaitingDeletion: Ref<number | null> = ref(null)
const isStopFollowingConfirmShown: Ref<boolean> = ref(false)
const actionError: Ref<string | null> = ref(null)

const litter: ComputedRef<LitterDetail | null> = computed((): LitterDetail | null => followUpsStore.openedLitter)
const selectedStatus: ComputedRef<FollowUpStatus | null> = computed((): FollowUpStatus | null => {
  const status: FollowUpStatus | undefined = litter.value?.follow_up?.status
  if (status === undefined) {
    return null
  }
  return status === 'new' ? 'to_contact' : status
})
const reminderMoment: ComputedRef<Date | null> = computed((): Date | null => {
  const nextReminderAt: string | null | undefined = litter.value?.follow_up?.next_reminder_at
  return nextReminderAt ? FrenchDate.parseApiDate(nextReminderAt) : null
})
const reminderInputValue: ComputedRef<string> = computed((): string =>
  reminderMoment.value ? FrenchDate.formatInputDayAndTime(reminderMoment.value) : '',
)
const reminderLabel: ComputedRef<string | null> = computed((): string | null =>
  reminderMoment.value ? FrenchDate.formatDayAndTime(reminderMoment.value) : null,
)

/**
 * Close the drawer when the user dismisses it.
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
 * Open the date and time picker on a click with a mouse; a tap opens the native picker by itself.
 *
 * @param event - Click on the reminder field.
 */
function openReminderPicker(event: MouseEvent): void {
  const input: EventTarget | null = event.currentTarget
  if (
    input instanceof HTMLInputElement &&
    'showPicker' in input &&
    window.matchMedia(FINE_POINTER_MEDIA_QUERY).matches
  ) {
    input.showPicker()
  }
}

/**
 * Save the reminder picked, a local day and time, or remove it when the picker was cleared.
 *
 * @param event - Change of the date and time input.
 */
async function changeReminder(event: Event): Promise<void> {
  const input: EventTarget | null = event.target
  if (!(input instanceof HTMLInputElement)) {
    return
  }
  await saveReminder(input.value === '' ? null : new Date(input.value).toISOString())
}

/**
 * Remove the reminder.
 */
async function clearReminder(): Promise<void> {
  await saveReminder(null)
}

/**
 * Save the reminder, keeping the status.
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
 * Add the typed note.
 */
async function addNote(): Promise<void> {
  const text: string = noteText.value.trim()
  if (text === '') {
    return
  }
  await tryChange(async (): Promise<void> => {
    await followUpsStore.addNote(text)
    noteText.value = ''
  })
}

/**
 * Delete a note once its deletion is confirmed.
 *
 * @param noteId - The note.
 */
async function removeNote(noteId: number): Promise<void> {
  await tryChange(async (): Promise<void> => {
    await followUpsStore.removeNote(noteId)
    noteIdAwaitingDeletion.value = null
  })
}

/**
 * Stop following the litter once confirmed; the drawer closes.
 */
async function stopFollowing(): Promise<void> {
  await tryChange((): Promise<void> => followUpsStore.stopFollowing())
}

/**
 * Write the day of a note.
 *
 * @param createdAt - Time of the note, from the API.
 * @returns « 24 octobre ».
 */
function formatNoteDay(createdAt: string): string {
  return FrenchDate.formatDayAndLongMonth(FrenchDate.parseApiDate(createdAt))
}

watch(
  (): string => route.fullPath,
  (): void => followUpsStore.close(),
)

watch(
  (): number | undefined => litter.value?.id,
  (): void => {
    noteText.value = ''
    noteIdAwaitingDeletion.value = null
    isStopFollowingConfirmShown.value = false
    actionError.value = null
  },
)
</script>
