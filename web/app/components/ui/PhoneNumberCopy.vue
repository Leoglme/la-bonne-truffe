<template>
  <div class="flex items-center justify-center gap-3.5">
    <span class="text-[17px] font-extrabold tracking-[0.02em] text-ink-secondary select-all">
      {{ props.phoneNumberLabel }}
    </span>
    <button
      type="button"
      class="inline-flex min-h-10 items-center gap-1.5 border-0 bg-transparent px-1 text-[15px] font-extrabold text-coral-text"
      @click="copyPhoneNumber"
    >
      <UIcon :name="hasJustCopied ? 'i-lucide-check' : 'i-lucide-copy'" class="size-4" />
      <span aria-live="polite">{{ hasJustCopied ? 'Copié' : 'Copier' }}</span>
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { UiPhoneNumberCopyProps } from '~/types/UiPhoneNumberCopy'
import { onBeforeUnmount, ref } from 'vue'

const props: UiPhoneNumberCopyProps = defineProps({
  phoneNumberLabel: { type: String, required: true },
})

const toast: ReturnType<typeof useToast> = useToast()

const COPIED_FEEDBACK_DURATION_IN_MILLISECONDS: number = 2000

const hasJustCopied: Ref<boolean> = ref(false)
let copiedFeedbackTimer: number | null = null

/**
 * Put the number in the clipboard, to dial it from the phone, and say so on the button for a moment.
 */
async function copyPhoneNumber(): Promise<void> {
  try {
    await navigator.clipboard.writeText(props.phoneNumberLabel)
  } catch {
    toast.add({ title: 'Copie impossible : recopie le numéro à la main', color: 'error' })
    return
  }
  hasJustCopied.value = true
  if (copiedFeedbackTimer !== null) {
    window.clearTimeout(copiedFeedbackTimer)
  }
  copiedFeedbackTimer = window.setTimeout((): void => {
    hasJustCopied.value = false
  }, COPIED_FEEDBACK_DURATION_IN_MILLISECONDS)
}

onBeforeUnmount((): void => {
  if (copiedFeedbackTimer !== null) {
    window.clearTimeout(copiedFeedbackTimer)
  }
})
</script>
