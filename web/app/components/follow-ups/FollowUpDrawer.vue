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
            <UiSegmentedControl
              :model-value="litter.follow_up.status"
              :options="FOLLOW_UP_STATUS_OPTIONS"
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
            class="min-h-11 rounded-2xl border-2 border-line-strong bg-card px-3.5 text-base text-ink"
            @change="changeReminder"
          />
        </label>

        <form class="flex flex-col gap-2" @submit.prevent="addNote">
          <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Nouvelle note</span>
          <textarea
            v-model="noteText"
            rows="3"
            placeholder="Appel du jour, liste d’attente, photos reçues…"
            class="rounded-2xl border-2 border-line-strong bg-card px-3.5 py-2.5 text-base text-ink"
          />
          <UButton type="submit" size="xl" class="self-start" :disabled="noteText.trim() === ''"
            >Ajouter la note</UButton
          >
        </form>

        <ul v-if="litter.follow_up.notes.length > 0" class="m-0 flex list-none flex-col gap-2.5 p-0">
          <li
            v-for="note in litter.follow_up.notes"
            :key="note.id"
            class="rounded-[14px] bg-cream px-3.5 py-2.5 text-[15px] leading-[1.45] text-ink-secondary"
          >
            <span class="block text-[13px] font-extrabold text-ink-label">{{ noteDay(note.created_at) }}</span>
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
import { FOLLOW_UP_STATUS_OPTIONS, isFollowUpStatus } from '~/constants/followUpOptions'
import { LitterPresentation } from '~/utils/litterPresentation'

const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()

const noteText: Ref<string> = ref('')

const litter: ComputedRef<LitterDetail | null> = computed((): LitterDetail | null => followUpsStore.openedLitter)
const reminderDay: ComputedRef<string> = computed((): string =>
  litter.value?.follow_up?.next_reminder_at ? litter.value.follow_up.next_reminder_at.slice(0, 10) : '',
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
 * Save a new status, keeping the reminder.
 *
 * @param value - Emitted status.
 */
async function changeStatus(value: string): Promise<void> {
  if (!isFollowUpStatus(value) || !litter.value?.follow_up) {
    return
  }
  await followUpsStore.saveFollowUp({
    status: value,
    next_reminder_at: litter.value.follow_up.next_reminder_at,
    last_contact_at: value === 'contacted' ? new Date().toISOString() : litter.value.follow_up.last_contact_at,
  })
}

/**
 * Save the reminder day (9 a.m. local time), or remove it.
 *
 * @param event - Change of the date input.
 */
async function changeReminder(event: Event): Promise<void> {
  const input: EventTarget | null = event.target
  if (!(input instanceof HTMLInputElement) || !litter.value?.follow_up) {
    return
  }
  const [year, month, day]: number[] = input.value.split('-').map(Number)
  const reminder: string | null =
    input.value === '' ? null : new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1, 9).toISOString()
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
 * The day of a note.
 *
 * @param createdAt - Naive UTC time of the note.
 * @returns « 24 octobre ».
 */
function noteDay(createdAt: string): string {
  const moment: Date = new Date(`${createdAt}Z`)
  const isoDay: string = `${moment.getFullYear()}-${String(moment.getMonth() + 1).padStart(2, '0')}-${String(moment.getDate()).padStart(2, '0')}`
  return LitterPresentation.longDay(isoDay)
}
</script>
