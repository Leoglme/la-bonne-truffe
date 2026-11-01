<template>
  <NuxtLink
    :to="`/eleveurs/${props.breeder.id}`"
    class="flex gap-3.5 rounded-card-compact bg-card p-3.5 text-ink no-underline shadow-card hover:text-ink md:gap-4 md:px-[18px] md:py-4"
  >
    <BreederAvatarTile
      :breeder="props.breeder"
      size-class="size-16 rounded-[18px] md:size-[72px] md:rounded-[20px]"
      text-class="text-[22px] md:text-2xl"
    />
    <span class="flex min-w-0 grow flex-col gap-[3px]">
      <span class="flex items-start justify-between gap-2">
        <span class="min-w-0 font-display text-lg leading-[1.2] font-semibold md:text-[21px]">
          {{ props.breeder.name }}
        </span>
        <UiCustomIcon
          v-if="props.breeder.is_followed"
          name="heart-filled"
          :size-in-pixels="22"
          class="size-5 shrink-0 text-coral md:size-[22px]"
          aria-label="Éleveur suivi"
          role="img"
        />
        <span
          v-else-if="props.isSourceShown && sourceLabel"
          class="inline-flex shrink-0 rounded-full bg-chip px-2.5 py-1 text-xs font-extrabold whitespace-nowrap text-ink-secondary"
        >
          {{ sourceLabel }}
        </span>
      </span>
      <span class="text-sm text-ink-muted md:text-[15px]">
        {{ BreederPresentation.buildPlaceLine(props.breeder, locationStore.position) }}
      </span>
      <span class="text-sm md:text-[15px]" :class="BREEDER_LITTER_STATUS_LINE_CLASSES[litterStatusLine.tone]">
        {{ litterStatusLine.text }}
      </span>
      <BreederChips :chips="chips" is-compact class="mt-1" />
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederCard, ListingSource } from '~/types/api'
import type { BreederChip, BreederLitterStatusLine } from '~/types/Breeder'
import type { BreederRowCardProps } from '~/types/BreederRowCard'
import { computed } from 'vue'
import { BREEDER_LITTER_STATUS_LINE_CLASSES } from '~/constants/breederOptions'
import { LISTING_SOURCE_LABELS } from '~/constants/litterLabels'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederRowCardProps = defineProps({
  breeder: { type: Object as PropType<BreederCard>, required: true },
  isSourceShown: { type: Boolean, default: false },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const litterStatusLine: ComputedRef<BreederLitterStatusLine> = computed((): BreederLitterStatusLine =>
  BreederPresentation.buildLitterStatusLine(props.breeder, new Date()),
)
const chips: ComputedRef<BreederChip[]> = computed((): BreederChip[] =>
  BreederPresentation.listChips(props.breeder, true),
)
const sourceLabel: ComputedRef<string | null> = computed((): string | null => {
  if (props.breeder.is_manual) {
    return 'Ajouté à la main'
  }
  const firstSource: ListingSource | undefined = props.breeder.sources[0]
  return firstSource === undefined ? null : LISTING_SOURCE_LABELS[firstSource]
})
</script>
