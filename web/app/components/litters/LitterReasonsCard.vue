<template>
  <div
    v-if="props.litter.reasons.length > 0"
    class="flex flex-col"
    :class="
      props.isInSidePanel
        ? ''
        : 'gap-2 rounded-[20px] bg-card px-4 py-3.5 shadow-card md:gap-3 md:rounded-card-compact md:px-[22px] md:py-5'
    "
  >
    <h2 v-if="!props.isInSidePanel" class="m-0 font-display text-[17px] font-semibold md:text-xl">
      Pourquoi {{ props.litter.score }} %
    </h2>
    <ul
      class="m-0 flex list-none flex-col p-0"
      :class="props.isInSidePanel ? 'gap-2 text-sm' : 'gap-1.5 text-sm md:gap-2.5 md:text-base'"
    >
      <li
        v-for="(reason, reasonIndex) in shownReasons"
        :key="reason.text"
        class="items-center"
        :class="[
          props.isInSidePanel ? 'flex gap-2.5' : 'gap-2.5 md:gap-3',
          !props.isInSidePanel && reasonIndex >= PHONE_REASON_LINE_LIMIT ? 'hidden md:flex' : 'flex',
        ]"
      >
        <span
          class="inline-flex shrink-0 items-center justify-center rounded-full bg-coral-pastel text-coral-text"
          :class="props.isInSidePanel ? 'size-[22px]' : 'size-[22px] md:size-[26px]'"
        >
          <UIcon name="i-lucide-check" :class="props.isInSidePanel ? 'size-3' : 'size-3 md:size-3.5'" />
        </span>
        {{ reason.text }}
      </li>
    </ul>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail, LitterReason } from '~/types/api'
import type { LitterReasonsCardProps } from '~/types/LitterReasonsCard'
import { computed } from 'vue'

const props: LitterReasonsCardProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const REASON_LINE_LIMIT: number = 5
const SIDE_PANEL_REASON_LINE_LIMIT: number = 3
const PHONE_REASON_LINE_LIMIT: number = 3

const shownReasons: ComputedRef<LitterReason[]> = computed((): LitterReason[] =>
  [...props.litter.reasons]
    .sort((first: LitterReason, second: LitterReason): number => second.points - first.points)
    .slice(0, props.isInSidePanel ? SIDE_PANEL_REASON_LINE_LIMIT : REASON_LINE_LIMIT),
)
</script>
