<template>
  <span>
    {{ LitterPresentation.buildPlace(props.litter) }} ·
    <LitterSexCounts v-if="props.litter.kind !== 'litter_expected'" :litter="props.litter" />
    <template v-else>{{ FollowUpPresentation.buildExpectedBirthPhrase(props.litter) }}</template>
    · {{ LitterPresentation.buildColorLabel(props.litter.colors, true).toLowerCase() }}
  </span>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { FollowUpSummaryLineProps } from '~/types/FollowUpSummaryLine'
import { FollowUpPresentation } from '~/utils/followUpPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: FollowUpSummaryLineProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
})
</script>
