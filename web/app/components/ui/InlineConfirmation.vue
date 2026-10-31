<template>
  <div class="flex flex-col gap-3 rounded-2xl bg-coral-pastel p-4">
    <p class="m-0 text-[15px] text-ink-secondary">
      <strong class="text-ink">{{ props.question }}</strong>
      {{ props.consequence }}
    </p>
    <div class="flex gap-2">
      <UButton color="neutral" variant="outline" class="flex-1 justify-center md:flex-none" @click="emit('cancelled')">
        Annuler
      </UButton>
      <UButton
        loading-auto
        class="min-h-12 flex-1 justify-center px-5 text-[15px] md:flex-none"
        @click="props.confirmAction"
      >
        {{ props.confirmLabel }}
      </UButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { UiInlineConfirmationEmits, UiInlineConfirmationProps } from '~/types/UiInlineConfirmation'

const props: UiInlineConfirmationProps = defineProps({
  question: { type: String, required: true },
  consequence: { type: String, required: true },
  confirmLabel: { type: String, required: true },
  confirmAction: { type: Function as PropType<() => Promise<void>>, required: true },
})

const emit: UiInlineConfirmationEmits = defineEmits<{
  (event: 'cancelled'): void
}>()
</script>
