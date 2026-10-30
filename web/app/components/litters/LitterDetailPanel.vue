<template>
  <aside
    aria-label="Portée sélectionnée"
    class="box-border w-[400px] shrink-0 flex-col gap-[18px] overflow-y-auto border-l border-line bg-card p-7"
  >
    <LitterTileFrame :litter="props.litter" class="h-[260px] overflow-hidden rounded-card-compact">
      <LitterVisual :litter="props.litter" :illustration-size-in-pixels="160" photo-position="center 30%" />
      <span
        v-if="photoBadge"
        class="absolute top-3.5 left-3.5 rounded-full bg-card px-3 py-[5px] text-[13px] leading-normal font-extrabold tracking-[0.02em] text-coral-text"
      >
        {{ photoBadge }}
      </span>
    </LitterTileFrame>
    <div class="flex items-start justify-between gap-3">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="m-0 font-display text-[26px] leading-[1.1] font-semibold">{{ props.litter.name }}</h2>
        <span class="text-sm text-ink-muted">{{ LitterDetailPresentation.buildTownAndDepartment(props.litter) }}</span>
      </div>
      <LitterScoreBubble :litter="props.litter" is-in-side-panel />
    </div>
    <LitterKeyFacts :litter="props.litter" is-in-side-panel />
    <LitterInfoChips :litter="props.litter" is-in-side-panel />
    <LitterColorConfirmation :litter="props.litter" is-in-side-panel />
    <LitterReasonsCard :litter="props.litter" is-in-side-panel />
    <div class="grow" />
    <div class="flex gap-2.5">
      <UButton
        v-if="primaryAction"
        :to="primaryAction.href"
        :target="primaryAction.isCall ? undefined : '_blank'"
        size="xl"
        class="min-h-[54px] grow justify-center px-4 text-base"
      >
        {{ primaryAction.label }}
      </UButton>
      <UButton
        color="neutral"
        variant="outline"
        size="lg"
        loading-auto
        :aria-haspopup="props.litter.follow_up ? 'dialog' : undefined"
        @click="littersStore.followOrOpenFollowUp(props.litter)"
      >
        {{ props.litter.follow_up ? 'Suivie' : 'Suivre' }}
      </UButton>
    </div>
  </aside>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterPrimaryAction } from '~/types/Litter'
import type { LitterDetailPanelProps } from '~/types/LitterDetailPanel'
import { computed } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterDetailPanelProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const photoBadge: ComputedRef<string | null> = computed((): string | null =>
  LitterDetailPresentation.buildPhotoBadge(props.litter, new Date()),
)
const primaryAction: ComputedRef<LitterPrimaryAction | null> = computed((): LitterPrimaryAction | null =>
  LitterDetailPresentation.resolvePrimaryAction(props.litter),
)
</script>
