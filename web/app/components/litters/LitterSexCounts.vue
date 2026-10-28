<template>
  <span v-if="unknownSexesLabel">{{ unknownSexesLabel }}</span>
  <span v-else>
    <span v-if="maleCount > 0" class="inline-flex items-center gap-1">
      {{ maleCount }}
      <UIcon name="i-lucide-mars" class="size-[1.2em] shrink-0 text-male" />
      <span class="sr-only">{{ FrenchText.pickForm(maleCount, 'mâle', 'mâles') }}</span>
    </span>
    <template v-if="maleCount > 0 && femaleCount > 0"> · </template>
    <span v-if="femaleCount > 0" class="inline-flex items-center gap-1">
      {{ femaleCount }}
      <UIcon name="i-lucide-venus" class="size-[1.2em] shrink-0 text-female" />
      <span class="sr-only">{{ FrenchText.pickForm(femaleCount, 'femelle', 'femelles') }}</span>
    </span>
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterSexCountsProps } from '~/types/LitterSexCounts'
import { computed } from 'vue'
import { FrenchText } from '~/utils/frenchText'

const props: LitterSexCountsProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
})

const maleCount: ComputedRef<number> = computed((): number => props.litter.male_count ?? 0)
const femaleCount: ComputedRef<number> = computed((): number => props.litter.female_count ?? 0)
const unknownSexesLabel: ComputedRef<string | null> = computed((): string | null => {
  if (props.litter.kind === 'litter_expected') {
    return 'À naître'
  }
  if (props.litter.male_count === null || props.litter.female_count === null) {
    return 'Sexes à confirmer'
  }
  if (maleCount.value === 0 && femaleCount.value === 0) {
    return 'Plus de chiot'
  }
  return null
})
</script>
