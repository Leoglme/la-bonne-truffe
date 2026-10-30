<template>
  <div class="flex items-center justify-between gap-3">
    <span class="text-[15px] font-bold md:text-[17px]">
      <slot name="label">{{ props.label }}</slot>
    </span>
    <span role="group" :aria-label="props.label" class="inline-flex items-center rounded-full bg-chip p-1">
      <button
        type="button"
        :aria-label="`Un de moins, ${props.label}`"
        :disabled="props.modelValue <= 0"
        class="inline-flex size-10 items-center justify-center rounded-full border-0 bg-card text-ink shadow-card disabled:opacity-40 disabled:shadow-none"
        @click="emit('update:modelValue', props.modelValue - 1)"
      >
        <UIcon name="i-lucide-minus" class="size-4" />
      </button>
      <span class="min-w-9 text-center font-display text-lg font-semibold" aria-live="polite">{{
        props.modelValue
      }}</span>
      <button
        type="button"
        :aria-label="`Un de plus, ${props.label}`"
        :disabled="props.modelValue >= props.maximum"
        class="inline-flex size-10 items-center justify-center rounded-full border-0 bg-card text-ink shadow-card disabled:opacity-40 disabled:shadow-none"
        @click="emit('update:modelValue', props.modelValue + 1)"
      >
        <UIcon name="i-lucide-plus" class="size-4" />
      </button>
    </span>
  </div>
</template>

<script lang="ts" setup>
import type { UiCountStepperEmits, UiCountStepperProps } from '~/types/UiCountStepper'

const props: UiCountStepperProps = defineProps({
  modelValue: { type: Number, required: true },
  label: { type: String, required: true },
  maximum: { type: Number, default: 20 },
})

const emit: UiCountStepperEmits = defineEmits<{
  (event: 'update:modelValue', value: number): void
}>()
</script>
