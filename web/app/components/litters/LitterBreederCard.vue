<template>
  <div
    v-if="breederName"
    class="flex flex-col gap-1"
    :class="
      props.isInSidePanel
        ? ''
        : 'rounded-[20px] bg-card px-4 py-3.5 shadow-card md:gap-1.5 md:rounded-card-compact md:px-[22px] md:py-5'
    "
  >
    <h2 v-if="!props.isInSidePanel" class="m-0 font-display text-[17px] font-semibold md:text-xl">Éleveur</h2>
    <span class="text-[15px] font-bold md:text-[17px]">{{ breederName }}</span>
    <span v-if="detailsLine" class="text-sm text-ink-muted md:text-[15px]">{{ detailsLine }}</span>
    <span v-if="props.litter.breeder?.has_affix" class="text-sm text-ink-muted md:text-[15px]">
      {{ BREEDER_AFFIX_LINE }}
    </span>
    <a
      v-if="props.isPhoneShown && props.litter.breeder?.phone_e164"
      :href="`tel:${props.litter.breeder.phone_e164}`"
      class="inline-flex min-h-11 items-center gap-1.5 self-start text-[15px] font-extrabold text-coral-text no-underline"
    >
      <UIcon name="i-lucide-phone" class="size-4" />
      {{ LitterDetailPresentation.buildBreederPhoneLabel(props.litter.breeder.phone_e164) }}
    </a>
    <a
      v-if="props.litter.breeder?.website"
      :href="props.litter.breeder.website"
      target="_blank"
      rel="noopener"
      class="inline-flex min-h-11 items-center gap-1.5 self-start text-[15px] font-extrabold text-coral-text no-underline"
    >
      Site de l’élevage
      <UIcon name="i-lucide-external-link" class="size-4" />
    </a>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterBreederCardProps } from '~/types/LitterBreederCard'
import { computed } from 'vue'
import { BREEDER_AFFIX_LINE } from '~/constants/litterLabels'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterBreederCardProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
  isPhoneShown: { type: Boolean, default: false },
})

const breederName: ComputedRef<string | null> = computed((): string | null =>
  props.litter.breeder ? LitterDetailPresentation.buildBreederName(props.litter.breeder) : null,
)
const detailsLine: ComputedRef<string | null> = computed((): string | null =>
  props.litter.breeder ? LitterDetailPresentation.buildBreederDetailsLine(props.litter.breeder) : null,
)
</script>
