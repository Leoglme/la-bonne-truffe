<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col gap-2">
      <label :for="noteFieldId" class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">
        Nouvelle note
      </label>
      <textarea
        :id="noteFieldId"
        v-model="noteText"
        rows="3"
        :placeholder="props.placeholder"
        class="rounded-2xl border-2 border-line-strong bg-card px-4 py-3 text-[17px] text-ink"
      />
      <UButton
        size="xl"
        class="mt-1 w-full justify-center md:w-auto md:self-start"
        :disabled="noteText.trim() === ''"
        loading-auto
        @click="addTypedNote"
      >
        Ajouter la note
      </UButton>
    </div>

    <ul v-if="props.notes.length > 0" class="m-0 flex list-none flex-col gap-2.5 p-0">
      <li
        v-for="note in props.notes"
        :key="note.id"
        class="rounded-[14px] bg-cream py-2.5 ps-3.5 pe-1.5 text-[15px] leading-[1.45] text-ink-secondary"
      >
        <div class="flex items-start gap-2">
          <span class="min-w-0 grow">
            <span class="block text-[13px] font-extrabold text-ink-label">
              {{ FrenchDate.formatApiDayAndLongMonth(note.created_at) }}
            </span>
            {{ note.text }}
          </span>
          <button
            v-if="noteIdAwaitingDeletion !== note.id"
            type="button"
            :aria-label="`Supprimer la note du ${FrenchDate.formatApiDayAndLongMonth(note.created_at)}`"
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
              @click="removeConfirmedNote(note.id)"
            >
              Supprimer
            </UButton>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script lang="ts" setup>
import type { PropType, Ref } from 'vue'
import type { FollowUpNoteLine, FollowUpNotesSectionProps } from '~/types/FollowUpNotesSection'
import { ref, useId } from 'vue'
import { FrenchDate } from '~/utils/frenchDate'

const props: FollowUpNotesSectionProps = defineProps({
  notes: { type: Array as PropType<FollowUpNoteLine[]>, required: true },
  placeholder: { type: String, default: 'Appel du jour, liste d’attente, photos reçues…' },
  addNote: { type: Function as PropType<(text: string) => Promise<void>>, required: true },
  removeNote: { type: Function as PropType<(noteId: number) => Promise<void>>, required: true },
})

const noteFieldId: string = useId()

const noteText: Ref<string> = ref('')
const noteIdAwaitingDeletion: Ref<number | null> = ref(null)

/**
 * Add the typed note, and clear the field once it is stored.
 */
async function addTypedNote(): Promise<void> {
  const text: string = noteText.value.trim()
  if (text === '') {
    return
  }
  await props.addNote(text)
  noteText.value = ''
}

/**
 * Delete a note once its deletion is confirmed.
 *
 * @param noteId - The note.
 */
async function removeConfirmedNote(noteId: number): Promise<void> {
  await props.removeNote(noteId)
  noteIdAwaitingDeletion.value = null
}
</script>
