<template>
  <p
    role="alert"
    class="m-0 flex items-center gap-2.5 rounded-2xl bg-coral-pastel px-3.5 py-[11px] text-sm font-bold text-ink md:text-[15px]"
  >
    <UIcon name="i-lucide-circle-alert" class="size-5 shrink-0 text-coral-text" />
    {{ props.message }}
  </p>
</template>

<script lang="ts" setup>
import type { UiErrorAlertProps } from '~/types/UiErrorAlert'

const props: UiErrorAlertProps = defineProps({
  message: { type: String, required: true },
})
</script>
