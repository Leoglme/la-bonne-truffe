<template>
  <span
    class="inline-flex h-6 items-center rounded-full px-2.5 text-xs leading-none font-bold"
    :class="NOTIFICATION_CHIP_CLASSES[chip.tone]"
  >
    {{ chip.label }}
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { NotificationKind } from '~/types/api'
import type { NotificationChip } from '~/types/Notification'
import type { NotificationKindChipProps } from '~/types/NotificationKindChip'
import { computed } from 'vue'
import { NOTIFICATION_CHIP_CLASSES, NOTIFICATION_CHIPS } from '~/constants/notificationKinds'

const props: NotificationKindChipProps = defineProps({
  kind: { type: String as PropType<NotificationKind>, required: true },
})

const chip: ComputedRef<NotificationChip> = computed((): NotificationChip => NOTIFICATION_CHIPS[props.kind])
</script>
