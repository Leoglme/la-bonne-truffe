<template>
  <NuxtLink
    :to="`/eleveurs/${props.breeder.id}`"
    class="relative flex flex-col gap-2.5 rounded-card-compact bg-card p-[18px] text-ink no-underline shadow-card hover:text-ink"
  >
    <UiCustomIcon
      v-if="props.breeder.is_followed"
      name="heart-filled"
      :size-in-pixels="22"
      class="absolute top-5 right-5 size-[22px] text-coral"
      aria-label="Éleveur suivi"
      role="img"
    />
    <BreederAvatarTile :breeder="props.breeder" size-class="size-[60px] rounded-[18px]" text-class="text-[22px]" />
    <span class="flex flex-col gap-[3px] pr-7">
      <span class="font-display text-[19px] leading-[1.2] font-semibold">{{ props.breeder.name }}</span>
      <span class="text-sm text-ink-muted">
        {{ BreederPresentation.buildPlaceLine(props.breeder, locationStore.position) }}
      </span>
      <span class="text-sm" :class="BREEDER_LITTER_STATUS_LINE_CLASSES[litterStatusLine.tone]">{{
        litterStatusLine.text
      }}</span>
    </span>
    <BreederChips :chips="chips" is-compact />
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederCard } from '~/types/api'
import type { BreederChip, BreederLitterStatusLine } from '~/types/Breeder'
import type { BreederGridCardProps } from '~/types/BreederGridCard'
import { computed } from 'vue'
import { BREEDER_LITTER_STATUS_LINE_CLASSES } from '~/constants/breederOptions'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederGridCardProps = defineProps({
  breeder: { type: Object as PropType<BreederCard>, required: true },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const litterStatusLine: ComputedRef<BreederLitterStatusLine> = computed((): BreederLitterStatusLine =>
  BreederPresentation.buildLitterStatusLine(props.breeder, new Date()),
)
const chips: ComputedRef<BreederChip[]> = computed((): BreederChip[] =>
  BreederPresentation.listChips(props.breeder, true),
)
</script>
