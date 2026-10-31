<template>
  <div v-if="parents.length > 0" class="flex flex-col gap-2 md:gap-2.5">
    <h2 class="m-0 mb-0.5 hidden font-display text-xl font-semibold md:block">Les parents</h2>
    <div
      v-for="parent in parents"
      :key="parent.role"
      class="flex flex-col gap-0.5 rounded-2xl bg-card px-3.5 py-3 shadow-card md:rounded-[20px] md:px-[18px] md:py-3.5"
    >
      <span class="text-[11px] font-extrabold text-ink-label md:text-[13px]">{{ parent.roleLabel }}</span>
      <span class="text-[15px] font-bold md:text-[17px]">{{ parent.name }}</span>
      <span v-if="parent.rating !== null" class="mt-1 flex items-center gap-2.5">
        <UiLevelGauge :level="parent.rating" :maximum-level="MAX_PARENT_RATING" />
        <span class="text-[13px] font-extrabold text-ink-secondary md:text-sm">{{ parent.ratingLabel }}</span>
      </span>
    </div>
    <p v-if="hasRatedParent" class="m-0 text-[13px] text-ink-muted md:text-sm">{{ PARENT_RATING_SCALE_NOTE }}</p>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail, LitterParent } from '~/types/api'
import type { LitterParentLine, LitterParentRole, LitterParentsListProps } from '~/types/LitterParentsList'
import { computed } from 'vue'
import { MAX_PARENT_RATING, PARENT_RATING_SCALE_NOTE, PARENT_ROLE_LABELS } from '~/constants/parentRatings'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterParentsListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const parents: ComputedRef<LitterParentLine[]> = computed((): LitterParentLine[] => {
  const lines: LitterParentLine[] = []
  if (props.litter.sire) {
    lines.push(buildParentLine('sire', props.litter.sire))
  }
  if (props.litter.dam) {
    lines.push(buildParentLine('dam', props.litter.dam))
  }
  return lines
})
const hasRatedParent: ComputedRef<boolean> = computed((): boolean =>
  parents.value.some((parent: LitterParentLine): boolean => parent.rating !== null),
)

/**
 * Build the line of a parent: role, name, and the Centrale Canine rating as a level name.
 *
 * @param role - Father or mother.
 * @param parent - The parent.
 * @returns The line; its rating stays null when the Centrale Canine gives none.
 */
function buildParentLine(role: LitterParentRole, parent: LitterParent): LitterParentLine {
  return {
    role,
    roleLabel: PARENT_ROLE_LABELS[role],
    name: parent.name,
    rating: parent.rating,
    ratingLabel: parent.rating === null ? null : LitterDetailPresentation.buildParentRatingLabel(parent.rating, role),
  }
}
</script>
