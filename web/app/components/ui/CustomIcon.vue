<template>
  <svg
    :width="props.sizeInPixels"
    :height="props.sizeInPixels"
    viewBox="0 0 24 24"
    :fill="definition.isFilled ? 'currentColor' : 'none'"
    :stroke="definition.isFilled ? undefined : 'currentColor'"
    :stroke-width="definition.isFilled ? undefined : props.strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <template v-for="(shape, index) in definition.shapes" :key="index">
      <path v-if="shape.element === 'path'" :d="shape.d" />
      <circle
        v-else-if="shape.element === 'circle'"
        :cx="shape.cx"
        :cy="shape.cy"
        :r="shape.r"
        :class="shape.fillClass"
      />
      <line v-else-if="shape.element === 'line'" :x1="shape.x1" :y1="shape.y1" :x2="shape.x2" :y2="shape.y2" />
      <ellipse v-else :cx="shape.cx" :cy="shape.cy" :rx="shape.rx" :ry="shape.ry" :class="shape.fillClass" />
    </template>
  </svg>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { CustomIconDefinition, CustomIconName, UiCustomIconProps } from '~/types/UiCustomIcon'
import { computed } from 'vue'
import { CUSTOM_ICONS } from '~/constants/customIcons'

const props: UiCustomIconProps = defineProps({
  name: { type: String as PropType<CustomIconName>, required: true },
  sizeInPixels: { type: Number, default: 24 },
  strokeWidth: { type: Number, default: 2 },
})

const definition: ComputedRef<CustomIconDefinition> = computed((): CustomIconDefinition => CUSTOM_ICONS[props.name])
</script>
