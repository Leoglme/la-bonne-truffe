<template>
  <div v-if="parents.length > 0" class="flex flex-col gap-2 md:gap-2.5">
    <div
      class="mb-0.5 items-baseline justify-between gap-3"
      :class="props.isTitleShownOnPhone ? 'flex' : 'hidden md:flex'"
    >
      <h2 class="m-0 font-display text-xl font-semibold">Les parents</h2>
      <span v-if="hasSitePhoto" class="text-[13px] font-bold text-ink-label md:text-sm">Photos de son site</span>
    </div>
    <div :class="props.isInWideLayout ? 'grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-3' : 'contents'">
      <div
        v-for="parent in parents"
        :key="parent.role"
        class="flex items-center gap-3 rounded-2xl bg-card py-3 pr-3.5 pl-3 shadow-card md:gap-4 md:rounded-[22px] md:pr-[18px]"
      >
        <DogPortrait
          :photo-url="parent.photoUrl"
          :color="parent.color"
          size-class="size-16 rounded-2xl md:size-[84px] md:rounded-[20px]"
          :illustration-size-in-pixels="PARENT_ILLUSTRATION_SIZE_IN_PIXELS"
        />
        <span class="flex min-w-0 grow flex-col gap-0.5">
          <span class="text-[11px] font-extrabold text-ink-label md:text-[13px]">{{ parent.roleLabel }}</span>
          <span class="text-[15px] font-bold md:text-[17px]">{{ parent.name }}</span>
          <span v-if="parent.colorAndGenotypeLine" class="text-[13px] text-ink-muted md:text-[15px]">
            {{ parent.colorAndGenotypeLine }}
          </span>
          <span v-if="parent.rating !== null" class="mt-1 flex items-center gap-2.5">
            <UiLevelGauge :level="parent.rating" :maximum-level="MAX_PARENT_RATING" />
            <span class="text-[13px] font-extrabold text-ink-secondary md:text-sm">{{ parent.ratingLabel }}</span>
          </span>
        </span>
      </div>
    </div>
    <p v-if="hasRatedParent" class="m-0 text-[13px] text-ink-muted md:text-sm">{{ PARENT_RATING_SCALE_NOTE }}</p>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { CoatColor, LitterDetail, LitterParent } from '~/types/api'
import type { FrenchGender } from '~/types/FrenchText'
import type { LitterParentLine, LitterParentRole, LitterParentsListProps } from '~/types/LitterParentsList'
import { computed } from 'vue'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { MAX_PARENT_RATING, PARENT_RATING_SCALE_NOTE, PARENT_ROLE_LABELS } from '~/constants/parentRatings'
import { GoldGeneticsPresentation } from '~/utils/goldGeneticsPresentation'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterParentsListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isTitleShownOnPhone: { type: Boolean, default: false },
  isInWideLayout: { type: Boolean, default: false },
})

const PARENT_ILLUSTRATION_SIZE_IN_PIXELS: number = 56

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
const hasSitePhoto: ComputedRef<boolean> = computed((): boolean =>
  parents.value.some((parent: LitterParentLine): boolean => parent.photoUrl !== null),
)

/**
 * Build the line of a parent: role, name, photo, colour and gold genotype, and its rating as a level name.
 *
 * @param role - Father or mother.
 * @param parent - The parent.
 * @returns The line; its rating stays null when the Centrale Canine gives none.
 */
function buildParentLine(role: LitterParentRole, parent: LitterParent): LitterParentLine {
  const gender: FrenchGender = role === 'dam' ? 'feminine' : 'masculine'
  const color: CoatColor | null = parent.color ?? null
  const lineParts: string[] = []
  if (color !== null && color !== 'inconnue') {
    lineParts.push(COAT_COLOR_LABELS[color])
  }
  const genotypeExplanation: string | null = GoldGeneticsPresentation.buildGenotypeExplanation(parent, gender)
  if (genotypeExplanation !== null) {
    lineParts.push(genotypeExplanation)
  }
  return {
    role,
    roleLabel: PARENT_ROLE_LABELS[role],
    name: parent.name,
    color,
    colorAndGenotypeLine: lineParts.length === 0 ? null : lineParts.join(' · '),
    photoUrl: parent.photo_url ?? null,
    rating: parent.rating,
    ratingLabel: parent.rating === null ? null : LitterDetailPresentation.buildParentRatingLabel(parent.rating, role),
  }
}
</script>
