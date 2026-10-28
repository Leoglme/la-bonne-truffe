<template>
  <NuxtLink
    :to="`/portees/${props.litter.id}`"
    class="flex shrink-0 flex-col overflow-hidden rounded-card-compact bg-coral-pastel text-ink no-underline hover:text-ink md:flex-row-reverse md:items-center md:gap-6 md:overflow-visible md:rounded-card md:px-8 md:py-7 lg:hidden"
  >
    <span
      class="relative block h-[170px] overflow-hidden md:size-[200px] md:shrink-0 md:rounded-card"
      :style="props.litter.photo_url ? undefined : { backgroundColor: tileColor }"
    >
      <img
        v-if="props.litter.photo_url"
        :src="props.litter.photo_url"
        alt="Chiot de la portée"
        class="block size-full object-cover"
        style="object-position: center 35%"
      />
      <span v-else class="flex size-full items-center justify-center">
        <CockerIllustration :coat="coat" :size-in-pixels="132" />
      </span>
      <span
        class="absolute top-3 left-3 rounded-full bg-card px-3 py-[5px] text-xs font-extrabold tracking-[0.02em] text-coral-text md:hidden"
      >
        NÉE CETTE NUIT
      </span>
    </span>
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
import type { CockerCoat } from '~/constants/cockerCoatPalettes'
import type { LitterCard } from '~/types/api'
import type { HomeBornLastNightCardProps } from '~/types/HomeBornLastNightCard'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { LitterPresentation } from '~/utils/litterPresentation'

/**
 * The « née cette nuit » card of the home screen (iPad and iPhone; the desktop shows it in the side
 * panel). The travel time of the mockup is not computed yet: the sentence keeps what is known.
 */
const props: HomeBornLastNightCardProps = defineProps({
  litter: { type: Object as PropType<LitterCard>, required: true },
})

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat => LitterPresentation.coatOf(props.litter.colors))
const tileColor: ComputedRef<string> = computed((): string => COCKER_COAT_PALETTES[coat.value].tile)

const title: ComputedRef<string> = computed((): string => {
  const where: string = props.litter.town
    ? `à ${props.litter.town}`
    : props.litter.department_code
      ? `dans le ${props.litter.department_code}`
      : ''
  return `Une portée ${LitterPresentation.colorInSentence(props.litter.colors)} ${where}`.trim()
})

const description: ComputedRef<string> = computed((): string => {
  const sentences: string[] = []
  const sexes: string | null = LitterPresentation.sexSentence(props.litter)
  if (sexes !== null) {
    sentences.push(`${sexes.charAt(0).toUpperCase()}${sexes.slice(1)}.`)
  }
  if (props.litter.available_from) {
    sentences.push(`Disponibles vers le ${LitterPresentation.longDay(props.litter.available_from)}.`)
  }
  return sentences.join(' ')
})

const compactDescription: ComputedRef<string> = computed((): string => {
  if (props.litter.male_count === null || props.litter.female_count === null) {
    return ''
  }
  const males: string = `${props.litter.male_count} mâle${props.litter.male_count > 1 ? 's' : ''}`
  const females: string = `${props.litter.female_count} femelle${props.litter.female_count > 1 ? 's' : ''}`
  return `${males}, ${females}.`
})
</script>
