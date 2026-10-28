<template>
  <svg
    :width="sizeInPixels"
    :height="sizeInPixels"
    viewBox="0 0 24 24"
    :fill="definition.isFilled ? 'currentColor' : 'none'"
    :stroke="definition.isFilled ? undefined : 'currentColor'"
    :stroke-width="definition.isFilled ? undefined : strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <template v-for="(shape, index) in definition.shapes" :key="index">
      <path v-if="shape.element === 'path'" :d="shape.d" :fill="shape.fill" />
      <circle v-else-if="shape.element === 'circle'" :cx="shape.cx" :cy="shape.cy" :r="shape.r" :fill="shape.fill" />
      <line v-else-if="shape.element === 'line'" :x1="shape.x1" :y1="shape.y1" :x2="shape.x2" :y2="shape.y2" />
      <ellipse
        v-else
        :cx="shape.cx"
        :cy="shape.cy"
        :rx="shape.rx"
        :ry="shape.ry"
        :fill="shape.fill"
        :opacity="shape.opacity"
      />
    </template>
  </svg>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { MockupIconDefinition, MockupIconName } from '~/constants/mockupIcons'
import type { UiMockupIconProps } from '~/types/UiMockupIcon'
import { computed } from 'vue'
import { MOCKUP_ICONS } from '~/constants/mockupIcons'

/** Decorative icon drawn exactly as in the mockup; the label belongs to the button or link around it. */
const props: UiMockupIconProps = defineProps({
  name: { type: String as PropType<MockupIconName>, required: true },
  sizeInPixels: { type: Number, default: 24 },
  strokeWidth: { type: Number, default: 2 },
})

const definition: ComputedRef<MockupIconDefinition> = computed((): MockupIconDefinition => MOCKUP_ICONS[props.name])
</script>
