<template>
  <button
    type="button"
    role="switch"
    :aria-checked="props.modelValue"
    :aria-label="props.label"
    :disabled="props.isDisabled"
    class="relative h-[34px] w-[58px] shrink-0 rounded-full border-0 p-0 transition-colors duration-200 ease-out disabled:cursor-not-allowed"
    :class="props.modelValue ? 'bg-coral' : 'bg-switch-off'"
    @click="emit('update:modelValue', !props.modelValue)"
  >
    <span
      class="absolute top-[3px] size-7 rounded-full bg-white shadow-[0_1px_3px_rgba(43,36,32,0.3)] transition-[left] duration-200 ease-out"
      :class="props.modelValue ? 'left-[27px]' : 'left-[3px]'"
      aria-hidden="true"
    />
  </button>
</template>

<script lang="ts" setup>
import type { UiToggleSwitchEmits, UiToggleSwitchProps } from '~/types/UiToggleSwitch'

/** On/off switch of the mockup: 58 × 34 pill, coral when on, 28 px knob, 200 ms ease-out. */
const props: UiToggleSwitchProps = defineProps({
  modelValue: { type: Boolean, required: true },
  label: { type: String, required: true },
  isDisabled: { type: Boolean, default: false },
})

const emit: UiToggleSwitchEmits = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
}>()
</script>
