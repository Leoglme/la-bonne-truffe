<template>
  <button
    type="button"
    :aria-pressed="props.isChecked"
    :disabled="props.isDisabled"
    class="flex min-h-14 w-full items-center gap-3 text-left text-[15px] font-bold text-ink disabled:opacity-60 md:text-[17px]"
    :class="
      props.isBordered
        ? ['rounded-tile-compact border-2 bg-card px-3.5', props.isChecked ? 'border-coral' : 'border-line']
        : 'border-0 bg-transparent px-0'
    "
  >
    <CockerIllustration :coat="ILLUSTRATED_COATS[props.color]" :size-in-pixels="40" />
    <span class="grow">{{ COAT_COLOR_LABELS[props.color] }}</span>
    <span
      class="inline-flex size-6 shrink-0 items-center justify-center rounded-full"
      :class="props.isChecked ? 'bg-coral text-white' : 'border-2 border-line-strong'"
      aria-hidden="true"
    >
      <UIcon v-if="props.isChecked" name="i-lucide-check" class="size-3.5" />
    </span>
  </button>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { CoatColor } from '~/types/api'
import type { CoatColorCheckButtonProps } from '~/types/CoatColorCheckButton'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { ILLUSTRATED_COATS } from '~/constants/cockerCoatPalettes'

const props: CoatColorCheckButtonProps = defineProps({
  color: { type: String as PropType<CoatColor>, required: true },
  isChecked: { type: Boolean, default: false },
  isDisabled: { type: Boolean, default: false },
  isBordered: { type: Boolean, default: false },
})
</script>
