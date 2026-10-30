<template>
  <NuxtLink
    :to="`/portees/${props.followUp.litter.id}`"
    class="flex w-full flex-col gap-3 rounded-card-compact bg-card p-3 text-left text-ink no-underline shadow-card hover:text-ink md:py-3.5 md:pr-[18px] md:pl-3.5"
    :class="props.isNoteShown && props.followUp.last_note ? 'pb-4' : ''"
  >
    <span class="flex w-full items-center gap-3.5 md:gap-4">
      <LitterTileFrame
        :litter="props.followUp.litter"
        class="size-16 rounded-tile-compact md:size-[72px] md:rounded-[20px]"
      >
        <LitterVisual :litter="props.followUp.litter" :illustration-size-in-pixels="52" />
      </LitterTileFrame>
      <span class="flex min-w-0 grow flex-col gap-0.5">
        <span class="font-display text-lg leading-[1.2] font-semibold md:text-[21px] md:leading-normal">
          {{ props.followUp.litter.name }}
        </span>
        <FollowUpSummaryLine :litter="props.followUp.litter" class="text-[13px] text-ink-muted md:text-[15px]" />
        <span v-if="lastContactLabel" class="text-[13px] text-ink-muted md:text-[15px]">{{ lastContactLabel }}</span>
        <span
          v-if="goneSinceLabel"
          class="mt-1 self-start rounded-full bg-coral-pastel px-2.5 py-1 text-xs font-extrabold text-coral-text md:px-3 md:py-1.5 md:text-[13px]"
        >
          {{ goneSinceLabel }}
        </span>
        <span
          v-if="reminderChip"
          class="mt-1 self-start rounded-full px-2.5 py-1 text-xs font-extrabold whitespace-nowrap md:hidden"
          :class="reminderChip.isUrgent ? 'bg-coral text-white' : 'bg-chip text-ink-secondary'"
        >
          {{ reminderChip.label }}
        </span>
      </span>
      <span
        v-if="reminderChip"
        class="hidden rounded-full px-3 py-1.5 text-[13px] font-extrabold whitespace-nowrap md:inline"
        :class="reminderChip.isUrgent ? 'bg-coral text-white' : 'bg-chip text-ink-secondary'"
      >
        {{ reminderChip.label }}
      </span>
    </span>
    <span
      v-if="props.isNoteShown && props.followUp.last_note"
      class="w-full rounded-[14px] bg-cream px-3.5 py-2.5 text-sm leading-[1.45] text-ink-secondary md:text-[15px]"
    >
      {{ props.followUp.last_note.text }}
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { FollowUpCard } from '~/types/api'
import type { FollowUpReminderChip } from '~/types/FollowUp'
import type { FollowUpLitterCardProps } from '~/types/FollowUpLitterCard'
import { computed } from 'vue'
import { FollowUpPresentation } from '~/utils/followUpPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: FollowUpLitterCardProps = defineProps({
  followUp: { type: Object as PropType<FollowUpCard>, required: true },
  isNoteShown: { type: Boolean, default: false },
})

const reminderChip: ComputedRef<FollowUpReminderChip | null> = computed((): FollowUpReminderChip | null =>
  FollowUpPresentation.buildReminderChip(props.followUp, new Date()),
)
const lastContactLabel: ComputedRef<string | null> = computed((): string | null =>
  FollowUpPresentation.buildLastContactLabel(props.followUp.last_contact_at),
)
const goneSinceLabel: ComputedRef<string | null> = computed((): string | null =>
  LitterPresentation.buildGoneSinceLabel(props.followUp.litter),
)
</script>
