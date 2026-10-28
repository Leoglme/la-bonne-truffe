<template>
  <div role="group" :aria-label="props.label" class="inline-flex shrink-0 rounded-full bg-chip p-1">
    <button
      v-for="option in props.options"
      :key="option.value"
      type="button"
      :aria-pressed="props.modelValue === option.value"
      :disabled="props.isDisabled"
      class="min-h-10 rounded-full border-0 px-3 text-[13px] font-extrabold whitespace-nowrap disabled:opacity-60 md:px-3.5 md:text-sm"
      :class="props.modelValue === option.value ? 'bg-ink text-cream' : 'bg-transparent text-ink-secondary'"
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { UiChoiceButtonsEmits, UiChoiceButtonsOption, UiChoiceButtonsProps } from '~/types/UiChoiceButtons'

const props: UiChoiceButtonsProps = defineProps({
  modelValue: { type: String, required: true },
  options: { type: Array as PropType<UiChoiceButtonsOption[]>, required: true },
  label: { type: String, required: true },
  isDisabled: { type: Boolean, default: false },
})

const emit: UiChoiceButtonsEmits = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()
</script>
