<template>
  <section class="flex flex-col gap-3">
    <h2 class="m-0 font-display text-[19px] font-semibold md:text-xl">Ses portées</h2>
    <p v-if="props.breeder.litters.length === 0" class="m-0 text-[15px] text-ink-muted">
      Aucune portée connue pour l’instant. Dès qu’il en déclare une, elle arrive ici.
    </p>
    <template v-else>
      <div :class="props.isInWideLayout ? 'grid grid-cols-[repeat(auto-fill,minmax(380px,1fr))] gap-3' : 'contents'">
        <LitterRowCard
          v-for="litter in shownLitters"
          :key="litter.id"
          :litter="litter"
          is-gold-puppy-odds-shown
          is-among-breeder-litters
        />
      </div>
      <button
        v-if="hiddenLittersCount > 0"
        type="button"
        class="inline-flex min-h-[52px] items-center justify-between gap-3 rounded-[20px] border-0 bg-card px-[18px] text-left text-[15px] font-bold text-ink shadow-card"
        @click="areAllLittersShown = true"
      >
        {{ hiddenLittersLabel }}
        <UIcon name="i-lucide-chevron-right" class="size-5 shrink-0 text-coral-text" />
      </button>
    </template>
    <a
      v-if="siteLittersLink"
      :href="siteLittersLink.href"
      target="_blank"
      rel="noopener"
      class="inline-flex min-h-[52px] items-center justify-between gap-3 rounded-[20px] bg-card px-[18px] text-[15px] font-bold text-ink-secondary no-underline shadow-card hover:text-ink-secondary"
    >
      {{ siteLittersLink.label }}
      <UIcon name="i-lucide-external-link" class="size-5 shrink-0 text-coral-text" />
    </a>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { BreederDetail, LitterCard } from '~/types/api'
import type { BreederSiteLink } from '~/types/Breeder'
import type { BreederLittersListProps } from '~/types/BreederLittersList'
import { computed, ref, watch } from 'vue'
import { BREEDER_LITTERS_SHOWN_COUNT } from '~/constants/breederOptions'
import { BreederPresentation } from '~/utils/breederPresentation'
import { FrenchText } from '~/utils/frenchText'

const props: BreederLittersListProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
  isInWideLayout: { type: Boolean, default: false },
})

const areAllLittersShown: Ref<boolean> = ref(false)

const shownLitters: ComputedRef<LitterCard[]> = computed((): LitterCard[] =>
  areAllLittersShown.value ? props.breeder.litters : props.breeder.litters.slice(0, BREEDER_LITTERS_SHOWN_COUNT),
)
const hiddenLittersCount: ComputedRef<number> = computed((): number =>
  Math.max(0, props.breeder.litters.length - shownLitters.value.length),
)
const hiddenLittersLabel: ComputedRef<string> = computed((): string => {
  const count: number = hiddenLittersCount.value
  return `${count} ${FrenchText.pickForm(count, 'autre portée', 'autres portées')}`
})
const siteLittersLink: ComputedRef<BreederSiteLink | null> = computed((): BreederSiteLink | null =>
  BreederPresentation.buildSiteLittersLink(props.breeder),
)

watch(
  (): number => props.breeder.id,
  (): void => {
    areAllLittersShown.value = false
  },
)
</script>
