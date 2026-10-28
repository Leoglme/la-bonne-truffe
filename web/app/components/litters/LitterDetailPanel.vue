<template>
  <aside
    aria-label="Portée sélectionnée"
    class="box-border w-[400px] shrink-0 flex-col gap-[18px] overflow-y-auto border-l border-line bg-card p-7"
  >
    <span
      class="relative block h-[260px] shrink-0 overflow-hidden rounded-card-compact"
      :style="{ backgroundColor: tileColor }"
    >
      <img
        v-if="props.litter.photo_url"
        :src="props.litter.photo_url"
        :alt="`Photo de la portée ${props.litter.name}`"
        class="block size-full object-cover"
        style="object-position: center 30%"
      />
      <span v-else class="flex size-full items-center justify-center">
        <CockerIllustration :coat="coat" :size-in-pixels="160" />
      </span>
      <span
        v-if="badge"
        class="absolute top-3.5 left-3.5 rounded-full bg-card px-3 py-[5px] text-[13px] leading-normal font-extrabold tracking-[0.02em] text-coral-text"
      >
        {{ badge }}
      </span>
    </span>
    <div class="flex items-start justify-between gap-3">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="m-0 font-display text-[26px] leading-[1.1] font-semibold">{{ props.litter.name }}</h2>
        <span class="text-sm text-ink-muted">{{ LitterDetailPresentation.placeLine(props.litter) }}</span>
      </div>
      <LitterScoreBubble :litter="props.litter" variant="panel" />
    </div>
    <LitterKeyFacts :litter="props.litter" variant="panel" />
    <LitterInfoChips :litter="props.litter" variant="panel" />
    <LitterReasonsCard :litter="props.litter" variant="panel" />
    <div class="grow" />
    <div class="flex gap-2.5">
      <a
        v-if="primaryAction"
        :href="primaryAction.href"
        :target="primaryAction.isCall ? undefined : '_blank'"
        :rel="primaryAction.isCall ? undefined : 'noopener'"
        class="inline-flex min-h-[54px] grow items-center justify-center gap-2 rounded-full bg-coral px-4 text-center text-base font-extrabold text-white no-underline hover:text-white"
      >
        {{ primaryAction.label }}
      </a>
      <button
        type="button"
        class="inline-flex min-h-[58px] items-center justify-center rounded-full border-2 border-ink bg-card px-[22px] text-base font-extrabold text-ink"
        :aria-pressed="props.litter.follow_up !== null"
        @click="littersStore.follow(props.litter.id)"
      >
        {{ props.litter.follow_up ? 'Suivie' : 'Suivre' }}
      </button>
    </div>
  </aside>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { CockerCoat } from '~/constants/cockerCoatPalettes'
import type { LitterDetail } from '~/types/api'
import type { LitterDetailPanelProps } from '~/types/LitterDetailPanel'
import type { LitterPrimaryAction } from '~/utils/litterDetailPresentation'
import { computed } from 'vue'
import { COCKER_COAT_PALETTES } from '~/constants/cockerCoatPalettes'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

/** Desktop side panel of the selected litter (design/mockup/Desktop.dc.html). */
const props: LitterDetailPanelProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const coat: ComputedRef<CockerCoat> = computed((): CockerCoat => LitterPresentation.coatOf(props.litter.colors))
const tileColor: ComputedRef<string> = computed((): string => COCKER_COAT_PALETTES[coat.value].tile)
const badge: ComputedRef<string | null> = computed((): string | null =>
  LitterDetailPresentation.badge(props.litter, new Date()),
)
const primaryAction: ComputedRef<LitterPrimaryAction | null> = computed((): LitterPrimaryAction | null =>
  LitterDetailPresentation.primaryAction(props.litter),
)
</script>
