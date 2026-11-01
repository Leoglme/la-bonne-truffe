<template>
  <button
    type="button"
    :aria-label="`Retour : ${props.label}`"
    class="inline-flex min-h-[52px] items-center gap-1.5 rounded-full border-0 bg-card pr-5 pl-3.5 text-base font-extrabold text-ink shadow-floating"
  >
    <UIcon name="i-lucide-chevron-left" class="size-[22px]" />
    {{ props.label }}
  </button>
</template>

<script lang="ts" setup>
import type { UiBackButtonProps } from '~/types/UiBackButton'

const props: UiBackButtonProps = defineProps({
  label: { type: String, required: true },
})
</script>
