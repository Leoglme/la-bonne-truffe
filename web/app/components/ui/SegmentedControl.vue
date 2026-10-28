<template>
  <div role="group" :aria-label="props.label" class="inline-flex shrink-0 rounded-full bg-chip p-1">
    <button
      v-for="option in props.options"
      :key="option.value"
      type="button"
      :aria-pressed="props.modelValue === option.value"
      class="min-h-10 rounded-full border-0 px-3 text-[13px] font-extrabold whitespace-nowrap md:px-3.5 md:text-sm"
      :class="props.modelValue === option.value ? 'bg-ink text-cream' : 'bg-transparent text-ink-secondary'"
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { UiSegmentedControlOption, UiSegmentedControlProps } from '~/types/UiSegmentedControl'

/** Pill group of exclusive choices (« Préférée · Acceptable · Ignorée »), each a pressed-state button. */
const props: UiSegmentedControlProps = defineProps({
  modelValue: { type: String, required: true },
  options: { type: Array as PropType<UiSegmentedControlOption[]>, required: true },
  label: { type: String, required: true },
})

const emit: UiSegmentedControlEmits = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()
</script>
