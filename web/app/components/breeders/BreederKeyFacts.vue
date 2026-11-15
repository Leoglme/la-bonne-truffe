<template>
  <section
    v-if="facts.length > 0"
    class="flex flex-col gap-3"
    :class="
      props.isInAside ? '' : 'rounded-[20px] bg-card p-4 shadow-card md:rounded-card-compact md:px-[22px] md:py-5'
    "
  >
    <h2 class="m-0 font-display text-lg font-semibold md:text-xl">En bref</h2>
    <ul class="m-0 flex list-none flex-col gap-2.5 p-0">
      <li v-for="fact in facts" :key="fact.key" class="flex items-start gap-3">
        <span
          class="inline-flex size-[34px] shrink-0 items-center justify-center rounded-xl bg-cream text-ink-secondary"
          aria-hidden="true"
        >
          <UIcon :name="fact.iconName" class="size-[18px]" />
        </span>
        <span class="pt-1.5 text-[15px] leading-[1.35] text-ink-secondary">
          <strong class="font-extrabold text-ink">{{ fact.boldStart }}</strong
          >{{ fact.sentenceEnd }}
        </span>
      </li>
    </ul>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederKeyFact } from '~/types/Breeder'
import type { BreederKeyFactsProps } from '~/types/BreederKeyFacts'
import { computed } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederKeyFactsProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
  isInAside: { type: Boolean, default: false },
})

const facts: ComputedRef<BreederKeyFact[]> = computed((): BreederKeyFact[] =>
  BreederPresentation.listKeyFacts(props.breeder, new Date()),
)
</script>
