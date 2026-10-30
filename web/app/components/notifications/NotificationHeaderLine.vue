<template>
  <span class="flex items-center justify-between gap-2">
    <NotificationKindChip :kind="props.kind" />
    <span class="inline-flex items-center gap-1.5 text-xs font-bold text-ink-muted">
      <span v-if="props.isUnread" class="size-2 rounded-full bg-coral" aria-hidden="true" />
      <span v-if="props.isUnread" class="sr-only">Nouvelle notification,</span>
      {{ timeLabel }}
    </span>
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { NotificationKind } from '~/types/api'
import type { NotificationHeaderLineProps } from '~/types/NotificationHeaderLine'
import { computed } from 'vue'
import { NotificationPresentation } from '~/utils/notificationPresentation'

const props: NotificationHeaderLineProps = defineProps({
  kind: { type: String as PropType<NotificationKind>, required: true },
  sentAt: { type: String, required: true },
  isUnread: { type: Boolean, required: true },
})

const timeLabel: ComputedRef<string> = computed((): string =>
  NotificationPresentation.buildTimeLabel(props.sentAt, new Date()),
)
</script>
