<template>
  <div class="flex flex-col gap-2">
    <label :for="reminderFieldId" class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">
      Rappel
    </label>
    <div class="relative">
      <input
        :id="reminderFieldId"
        type="datetime-local"
        :value="reminderInputValue"
        :disabled="props.isDisabled"
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
        :disabled="props.isDisabled"
        class="absolute end-1 top-1/2 z-20 inline-flex size-11 -translate-y-1/2 items-center justify-center rounded-full border-0 bg-transparent text-ink-muted"
        @click="emit('update:modelValue', null)"
      >
        <UIcon name="i-lucide-x" class="size-5" />
      </button>
    </div>
    <span class="text-sm text-ink-muted">Une notification te prévient à cette heure-là.</span>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { FollowUpReminderFieldEmits, FollowUpReminderFieldProps } from '~/types/FollowUpReminderField'
import { computed, useId } from 'vue'
import { FrenchDate } from '~/utils/frenchDate'

const FINE_POINTER_MEDIA_QUERY: string = '(pointer: fine)'

const props: FollowUpReminderFieldProps = defineProps({
  modelValue: { type: String as PropType<string | null>, default: null },
  isDisabled: { type: Boolean, default: false },
})

const emit: FollowUpReminderFieldEmits = defineEmits<{
  (event: 'update:modelValue', nextReminderAt: string | null): void
}>()

const reminderFieldId: string = useId()

const reminderMoment: ComputedRef<Date | null> = computed((): Date | null =>
  props.modelValue ? FrenchDate.parseApiDate(props.modelValue) : null,
)
const reminderInputValue: ComputedRef<string> = computed((): string =>
  reminderMoment.value ? FrenchDate.formatInputDayAndTime(reminderMoment.value) : '',
)
const reminderLabel: ComputedRef<string | null> = computed((): string | null =>
  reminderMoment.value ? FrenchDate.formatDayAndTime(reminderMoment.value) : null,
)

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
 * Hand over the reminder picked, a local day and time, or null when the picker was cleared.
 *
 * @param event - Change of the date and time input.
 */
function changeReminder(event: Event): void {
  const input: EventTarget | null = event.target
  if (!(input instanceof HTMLInputElement)) {
    return
  }
  emit('update:modelValue', input.value === '' ? null : new Date(input.value).toISOString())
}
</script>
