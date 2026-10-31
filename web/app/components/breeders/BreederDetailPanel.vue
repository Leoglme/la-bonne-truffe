<template>
  <aside
    aria-label="Fiche de l’éleveur"
    class="box-border flex w-[400px] shrink-0 flex-col overflow-hidden border-l border-line bg-card"
  >
    <div class="relative h-[170px] shrink-0 overflow-hidden">
      <BreederCover :breeder="props.breeder" :illustration-size-in-pixels="120" />
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="solid"
        size="md"
        square
        aria-label="Fermer la fiche"
        class="absolute top-4 left-4 size-11 min-h-11 justify-center rounded-full bg-card p-0 text-ink shadow-floating-over-photo hover:bg-card"
        @click="emit('close')"
      />
      <BreederFollowHeartButton :breeder="props.breeder" is-in-side-panel class="absolute top-4 right-4" />
    </div>
    <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-[22px] pt-[22px] pb-4">
      <div class="flex items-center gap-3">
        <BreederAvatarTile :breeder="props.breeder" size-class="size-[52px] rounded-2xl" text-class="text-xl" />
        <div class="flex min-w-0 flex-col gap-0.5">
          <h2 class="m-0 font-display text-[22px] leading-[1.1] font-semibold">{{ props.breeder.name }}</h2>
          <span class="text-[13px] text-ink-muted">
            {{ BreederPresentation.buildIdentityLine(props.breeder, locationStore.position) }}
          </span>
        </div>
      </div>
      <BreederChips :chips="chips" is-compact />
      <BreederStats :breeder="props.breeder" is-in-side-panel />
      <BreederLittersList :breeder="props.breeder" is-in-side-panel />
      <BreederColorShares :breeder="props.breeder" is-in-side-panel />
      <BreederFollowCard :breeder="props.breeder" is-in-side-panel />
      <NuxtLink
        :to="`/eleveurs/${props.breeder.id}`"
        class="inline-flex min-h-11 items-center gap-1.5 self-start text-[15px] font-extrabold text-coral-text no-underline"
      >
        Voir la fiche complète
        <UIcon name="i-lucide-chevron-right" class="size-4" />
      </NuxtLink>
    </div>
    <div v-if="primaryAction" class="flex shrink-0 border-t border-line px-[22px] pt-3 pb-[22px]">
      <UButton
        :to="primaryAction.href"
        :target="primaryAction.isCall ? undefined : '_blank'"
        size="xl"
        class="min-h-[52px] w-full justify-center gap-2 px-4 text-base"
      >
        <template #leading>
          <UiCustomIcon v-if="primaryAction.isCall" name="phone" :size-in-pixels="18" :stroke-width="2.2" />
          <UIcon v-else name="i-lucide-external-link" class="size-[18px]" />
        </template>
        {{ primaryAction.label }}
      </UButton>
    </div>
  </aside>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederChip } from '~/types/Breeder'
import type { BreederDetailPanelEmits, BreederDetailPanelProps } from '~/types/BreederDetailPanel'
import type { PrimaryAction } from '~/types/PrimaryAction'
import { computed } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederDetailPanelProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
})

const emit: BreederDetailPanelEmits = defineEmits<{
  (event: 'close'): void
}>()

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const chips: ComputedRef<BreederChip[]> = computed((): BreederChip[] =>
  BreederPresentation.listDetailChips(props.breeder),
)
const primaryAction: ComputedRef<PrimaryAction | null> = computed((): PrimaryAction | null =>
  BreederPresentation.resolvePrimaryAction(props.breeder),
)
</script>
