<template>
  <span
    class="inline-flex items-center gap-1"
    role="img"
    :aria-label="`Niveau ${props.level} sur ${props.maximumLevel}`"
  >
    <span
      v-for="step in props.maximumLevel"
      :key="step"
      class="size-2 rounded-full"
      :class="step <= props.level ? 'bg-coral' : 'bg-line-strong'"
    />
  </span>
</template>

<script lang="ts" setup>
import type { UiLevelGaugeProps } from '~/types/UiLevelGauge'

const props: UiLevelGaugeProps = defineProps({
  level: { type: Number, required: true },
  maximumLevel: { type: Number, required: true },
})
</script>
