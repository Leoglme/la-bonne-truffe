<template>
  <section v-if="lines.length > 0" class="flex flex-col gap-3">
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="m-0 font-display text-[19px] font-semibold md:text-xl">Ses prochaines portées</h2>
      <span class="text-[13px] text-ink-label md:text-sm">Estimation de la truffe</span>
    </div>
    <div :class="props.isInWideLayout ? 'grid grid-cols-[repeat(auto-fill,minmax(380px,1fr))] gap-3' : 'contents'">
      <div v-for="line in lines" :key="line.key" class="flex gap-3.5 rounded-card-compact bg-card p-3 shadow-card">
        <span
          class="relative box-border flex size-[118px] shrink-0 items-center justify-center rounded-tile-compact border-[3px] border-dashed border-coral-text/35"
          :class="LitterPresentation.resolveTileClass(line.colors)"
        >
          <CockerIllustration
            :coat="LitterPresentation.resolveIllustrationCoat(line.colors)"
            :size-in-pixels="84"
            aria-hidden="true"
          />
          <span
            class="absolute bottom-2 left-2 rounded-full bg-card px-[9px] py-[3px] text-[13px] leading-[1.45] font-extrabold text-coral-text"
          >
            Probable
          </span>
        </span>
        <span class="flex min-w-0 grow flex-col justify-center gap-1">
          <span class="font-display text-lg leading-[1.2] font-semibold">{{ line.title }}</span>
          <span class="text-[13px] text-ink-muted">{{ line.motherLine }}</span>
          <span class="mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-[13px] font-bold text-ink-secondary">
            <LitterColorBadge :colors="line.colors" is-label-always-short />
            <span v-if="line.hasKnownColors" class="text-ink-muted">probable</span>
          </span>
        </span>
      </div>
    </div>
    <p class="m-0 text-sm leading-[1.45] text-ink-muted md:text-[15px]">
      Une chienne a en général une portée par an, comptée depuis sa dernière. Appelle maintenant pour te placer sur la
      liste d’attente.
    </p>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { ProbableLitter } from '~/types/api'
import type { ProbableLitterLine } from '~/types/Breeder'
import type { BreederProbableLittersListProps } from '~/types/BreederProbableLittersList'
import { computed } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: BreederProbableLittersListProps = defineProps({
  probableLitters: { type: Array as PropType<ProbableLitter[]>, required: true },
  isInWideLayout: { type: Boolean, default: false },
})

const lines: ComputedRef<ProbableLitterLine[]> = computed((): ProbableLitterLine[] =>
  BreederPresentation.listProbableLitterLines(props.probableLitters, new Date()),
)
</script>
