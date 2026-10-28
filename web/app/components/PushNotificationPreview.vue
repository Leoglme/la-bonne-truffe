<template>
  <div
    aria-hidden="true"
    class="flex items-center gap-2.5 rounded-[18px] bg-card py-2.5 ps-2.5 pe-3.5 shadow-straddling-photo md:gap-3.5 md:rounded-3xl md:py-3.5 md:ps-3.5 md:pe-[18px]"
  >
    <UiAppIcon class="size-[34px] md:size-11" />
    <div class="flex min-w-0 flex-1 flex-col leading-[1.3] md:leading-[1.35]">
      <span class="flex justify-between gap-2 text-xs text-ink-muted md:text-[13px]">
        <span class="font-extrabold text-ink-secondary">La Bonne Truffe</span>
        <span>maintenant</span>
      </span>
      <span class="text-[13px] font-extrabold md:text-[15px]">{{ props.title }}</span>
      <span class="truncate text-[13px] md:text-[15px]">{{ props.body }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { PushNotificationPreviewProps } from '~/types/PushNotificationPreview'

const props: PushNotificationPreviewProps = defineProps({
  title: { type: String, required: true },
  body: { type: String, required: true },
})
</script>
