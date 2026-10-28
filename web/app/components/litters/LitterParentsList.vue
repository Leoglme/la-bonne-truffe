<template>
  <div v-if="parents.length > 0" class="flex flex-col gap-2 md:gap-2.5">
    <h2 class="m-0 mb-0.5 hidden font-display text-xl font-semibold md:block">Les parents</h2>
    <div
      v-for="parent in parents"
      :key="parent.role"
      class="flex items-center justify-between gap-2.5 rounded-2xl bg-card px-3.5 py-3 shadow-card md:gap-3 md:rounded-[20px] md:px-[18px] md:py-3.5"
    >
      <span class="flex flex-col">
        <span class="text-[11px] font-extrabold text-ink-label md:text-[13px]">{{ parent.role }}</span>
        <span class="text-[15px] font-bold md:text-[17px]">{{ parent.name }}</span>
      </span>
      <span class="text-xs font-extrabold whitespace-nowrap text-ink-secondary md:hidden">{{
        parent.compactRating
      }}</span>
      <span
        class="hidden rounded-full bg-chip px-3 py-1.5 text-sm font-extrabold whitespace-nowrap text-ink-secondary md:inline"
      >
        {{ parent.rating }}
      </span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail, LitterParent } from '~/types/api'
import type { LitterDetailVariant } from '~/types/LitterDetailVariant'
import type { LitterParentsListProps } from '~/types/LitterParentsList'
import { computed } from 'vue'

/** One parent line: role, name and Centrale Canine rating. */
type ParentLine = {
  role: string
  name: string
  rating: string
  compactRating: string
}

/** Father and mother of the litter with their rating (« Cotation 4 / 6 »). */
const props: LitterParentsListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  variant: { type: String as PropType<LitterDetailVariant>, default: 'responsive' },
})

/**
 * Turn a parent into its line.
 *
 * @param role - « PÈRE » or « MÈRE ».
 * @param parent - The parent.
 * @returns The line.
 */
function toParentLine(role: string, parent: LitterParent): ParentLine {
  return {
    role,
    name: parent.name,
    rating: parent.rating === null ? 'Sans cotation' : `Cotation ${parent.rating} / 6`,
    compactRating: parent.rating === null ? 'Sans cot.' : `Cot. ${parent.rating} / 6`,
  }
}

const parents: ComputedRef<ParentLine[]> = computed((): ParentLine[] => {
  const lines: ParentLine[] = []
  if (props.litter.sire) {
    lines.push(toParentLine('PÈRE', props.litter.sire))
  }
  if (props.litter.dam) {
    lines.push(toParentLine('MÈRE', props.litter.dam))
  }
  return lines
})
</script>
