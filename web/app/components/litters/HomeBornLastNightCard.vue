<template>
  <NuxtLink
    :to="`/portees/${props.litter.id}`"
    class="flex shrink-0 flex-col overflow-hidden rounded-card-compact bg-coral-pastel text-ink no-underline hover:text-ink md:flex-row-reverse md:items-center md:gap-6 md:overflow-visible md:rounded-card md:px-8 md:py-7 lg:hidden"
  >
    <LitterTileFrame :litter="props.litter" class="h-[170px] overflow-hidden md:size-[200px] md:rounded-card">
      <LitterVisual :litter="props.litter" :illustration-size-in-pixels="132" photo-position="center 35%" />
      <span
        class="absolute top-3 left-3 rounded-full bg-card px-3 py-[5px] text-xs font-extrabold tracking-[0.02em] text-coral-text md:hidden"
      >
        NÉE CETTE NUIT
      </span>
    </LitterTileFrame>
    <span class="flex min-w-0 grow flex-col gap-1.5 px-[18px] pt-3.5 pb-[18px] md:gap-2.5 md:p-0">
      <span
        class="hidden self-start rounded-full bg-card px-3.5 py-1.5 text-sm leading-normal font-extrabold tracking-[0.02em] text-coral-text md:inline-flex"
      >
        NÉE CETTE NUIT
      </span>
      <span class="font-display text-[22px] leading-[1.15] font-semibold md:text-[30px]">{{ title }}</span>
      <span class="text-sm text-ink-secondary md:hidden">{{ compactDescription }}</span>
      <span class="hidden text-[17px] text-ink-secondary md:inline">{{ description }}</span>
      <span
        class="mt-1 inline-flex min-h-11 items-center justify-center self-start rounded-full bg-coral px-[18px] text-[15px] font-extrabold text-white md:mt-1.5 md:min-h-[52px] md:px-6 md:text-lg"
      >
        Voir la portée
      </span>
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterCard } from '~/types/api'
import type { HomeBornLastNightCardProps } from '~/types/HomeBornLastNightCard'
import { computed } from 'vue'
import { FrenchDate } from '~/utils/frenchDate'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: HomeBornLastNightCardProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
})

const title: ComputedRef<string> = computed((): string => {
  const litterWithColor: string = `Une portée ${LitterPresentation.buildColorPhrase(props.litter.colors)}`
  if (props.litter.town) {
    return `${litterWithColor} à ${props.litter.town}`
  }
  if (props.litter.department_code) {
    return `${litterWithColor} dans le ${props.litter.department_code}`
  }
  return litterWithColor
})

const description: ComputedRef<string> = computed((): string => {
  const sentences: string[] = []
  const sexCounts: string[] = LitterPresentation.listSexCounts(props.litter)

  if (sexCounts.length > 0) {
    sentences.push(`${sexCounts.join(' et ')}.`)
  }
  if (props.litter.available_from) {
    const availableDay: Date = FrenchDate.parseDay(props.litter.available_from)
    sentences.push(`Disponibles vers le ${FrenchDate.formatDayAndLongMonth(availableDay)}.`)
  }
  return sentences.join(' ')
})

const compactDescription: ComputedRef<string> = computed((): string => {
  const sexCounts: string[] = LitterPresentation.listSexCounts(props.litter)
  if (sexCounts.length === 0) {
    return ''
  }
  return `${sexCounts.join(', ')}.`
})
</script>
