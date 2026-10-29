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
      <span
        v-if="parent.rating"
        class="shrink-0 rounded-full bg-chip px-2.5 py-1 text-xs font-extrabold whitespace-nowrap text-ink-secondary md:px-3 md:py-1.5 md:text-sm"
      >
        {{ parent.rating }}
      </span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail, LitterParent } from '~/types/api'
import type { LitterParentLine, LitterParentsListProps } from '~/types/LitterParentsList'
import { computed } from 'vue'

const props: LitterParentsListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const parents: ComputedRef<LitterParentLine[]> = computed((): LitterParentLine[] => {
  const lines: LitterParentLine[] = []
  if (props.litter.sire) {
    lines.push(buildParentLine('PÈRE', props.litter.sire))
  }
  if (props.litter.dam) {
    lines.push(buildParentLine('MÈRE', props.litter.dam))
  }
  return lines
})

/**
 * Build the line of a parent: role, name and Centrale Canine rating.
 *
 * @param role - « PÈRE » or « MÈRE ».
 * @param parent - The parent.
 * @returns The line; its rating stays null when the Centrale Canine gives none.
 */
function buildParentLine(role: string, parent: LitterParent): LitterParentLine {
  return {
    role,
    name: parent.name,
    rating: parent.rating === null ? null : `Cotation ${parent.rating} / 6`,
  }
}
</script>
