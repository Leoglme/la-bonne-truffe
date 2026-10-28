<template>
  <UDrawer
    :open="litter !== null"
    :title="litter?.name ?? ''"
    description="Où en est l’échange"
    @update:open="onOpenChange"
  >
    <template #body>
      <div v-if="litter && litter.follow_up" class="flex flex-col gap-5 pb-6">
        <div class="flex flex-col gap-2">
          <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Statut</span>
          <div class="flex flex-wrap gap-2">
            <UiChoiceButtons
              :model-value="litter.follow_up.status"
              :options="FOLLOW_UP_STATUS_OPTIONS"
              :is-disabled="followUpsStore.isSaving"
              label="Statut de l’échange"
              class="flex-wrap"
              @update:model-value="changeStatus"
            />
          </div>
        </div>

        <label class="flex flex-col gap-2">
          <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Prochain rappel</span>
          <input
            type="date"
            :value="reminderDay"
            :disabled="followUpsStore.isSaving"
            class="min-h-11 rounded-2xl border-2 border-line-strong bg-card px-3.5 text-base text-ink disabled:opacity-60"
            @change="changeReminder"
          />
        </label>

        <div class="flex flex-col gap-2">
          <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Nouvelle note</span>
          <textarea
            v-model="noteText"
            rows="3"
            placeholder="Appel du jour, liste d’attente, photos reçues…"
            class="rounded-2xl border-2 border-line-strong bg-card px-3.5 py-2.5 text-base text-ink"
          />
          <UButton size="xl" class="self-start" :disabled="noteText.trim() === ''" loading-auto @click="addNote">
            Ajouter la note
          </UButton>
        </div>

        <ul v-if="litter.follow_up.notes.length > 0" class="m-0 flex list-none flex-col gap-2.5 p-0">
          <li
            v-for="note in litter.follow_up.notes"
            :key="note.id"
            class="rounded-[14px] bg-cream px-3.5 py-2.5 text-[15px] leading-[1.45] text-ink-secondary"
          >
            <span class="block text-[13px] font-extrabold text-ink-label">{{ formatNoteDay(note.created_at) }}</span>
            {{ note.text }}
          </li>
        </ul>

        <NuxtLink :to="`/portees/${litter.id}`" class="self-start text-[15px] font-extrabold">Voir la portée</NuxtLink>
      </div>
    </template>
  </UDrawer>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { LitterDetail } from '~/types/api'
import { computed, ref } from 'vue'
import { FOLLOW_UP_STATUS_OPTIONS } from '~/constants/followUpOptions'
import { ChoiceValues } from '~/utils/choiceValues'
import { FrenchDate } from '~/utils/frenchDate'

const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()

const REMINDER_HOUR: number = 9

const noteText: Ref<string> = ref('')

const litter: ComputedRef<LitterDetail | null> = computed((): LitterDetail | null => followUpsStore.openedLitter)
const reminderDay: ComputedRef<string> = computed((): string => {
  const nextReminderAt: string | null | undefined = litter.value?.follow_up?.next_reminder_at
  if (!nextReminderAt) {
    return ''
  }
  return FrenchDate.formatInputDay(FrenchDate.parseApiDate(nextReminderAt))
})

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
 * Save a new status, keeping the reminder.
 *
 * @param value - Emitted status.
 */
async function changeStatus(value: string): Promise<void> {
  if (!ChoiceValues.isFollowUpStatus(value) || !litter.value?.follow_up) {
    return
  }
  await followUpsStore.saveFollowUp({
    status: value,
    next_reminder_at: litter.value.follow_up.next_reminder_at,
    last_contact_at: value === 'contacted' ? new Date().toISOString() : litter.value.follow_up.last_contact_at,
  })
}

/**
 * Save the reminder day, at the reminder hour in local time, or remove it.
 *
 * @param event - Change of the date input.
 */
async function changeReminder(event: Event): Promise<void> {
  const input: EventTarget | null = event.target
  if (!(input instanceof HTMLInputElement) || !litter.value?.follow_up) {
    return
  }
  let reminder: string | null = null

  if (input.value !== '') {
    const reminderDate: Date = FrenchDate.parseDay(input.value)
    reminderDate.setHours(REMINDER_HOUR)
    reminder = reminderDate.toISOString()
  }
  await followUpsStore.saveFollowUp({
    status: litter.value.follow_up.status,
    next_reminder_at: reminder,
    last_contact_at: litter.value.follow_up.last_contact_at,
  })
}

/**
 * Add the typed note.
 */
async function addNote(): Promise<void> {
  const text: string = noteText.value.trim()
  if (text === '') {
    return
  }
  await followUpsStore.addNote(text)
  noteText.value = ''
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
</script>
