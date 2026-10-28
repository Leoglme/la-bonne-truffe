<template>
  <span
    aria-hidden="true"
    class="absolute right-3.5 bottom-3.5 flex size-12 items-center justify-center rounded-full bg-coral text-card md:right-[22px] md:bottom-[22px] md:size-16"
  >
    <UIcon :name="props.iconName" class="size-[22px] md:size-7" />
  </span>
</template>

<script lang="ts" setup>
import type { AuthVisualBadgeProps } from '~/types/AuthVisualBadge'

const props: AuthVisualBadgeProps = defineProps({
  iconName: { type: String, required: true },
})
</script>
