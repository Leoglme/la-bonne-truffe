<template>
  <span v-if="props.chips.length > 0" class="flex flex-wrap gap-1.5 md:gap-2">
    <span
      v-for="chip in props.chips"
      :key="chip.label"
      class="inline-flex rounded-full font-extrabold whitespace-nowrap"
      :class="[BREEDER_CHIP_CLASSES[chip.tone], props.isCompact ? 'px-2.5 py-1 text-xs' : 'px-3.5 py-2 text-[15px]']"
    >
      {{ chip.label }}
    </span>
  </span>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { BreederChip } from '~/types/Breeder'
import type { BreederChipsProps } from '~/types/BreederChips'
import { BREEDER_CHIP_CLASSES } from '~/constants/breederOptions'

const props: BreederChipsProps = defineProps({
  chips: { type: Array as PropType<BreederChip[]>, required: true },
  isCompact: { type: Boolean, default: false },
})
</script>
