<template>
  <div
    v-if="mapDestination"
    class="flex items-center justify-between gap-2.5"
    :class="
      props.isInSidePanel
        ? 'rounded-2xl bg-cream px-3 py-2.5'
        : 'rounded-2xl bg-card px-3.5 py-3 shadow-card md:gap-3 md:rounded-[20px] md:px-[18px] md:py-3.5'
    "
  >
    <span class="flex min-w-0 flex-col">
      <span
        class="text-[11px] font-extrabold text-ink-label uppercase"
        :class="props.isInSidePanel ? '' : 'md:text-[13px] md:tracking-[0.04em]'"
      >
        Lieu
      </span>
      <span class="text-[15px] font-bold" :class="props.isInSidePanel ? '' : 'md:text-[17px]'">
        {{ mapDestination.placeName }}
      </span>
      <span v-if="distanceLabel" class="text-[13px] text-ink-muted">{{ distanceLabel }}</span>
    </span>
    <UButton
      icon="i-lucide-map"
      color="neutral"
      variant="outline"
      size="lg"
      square
      aria-label="Voir sur la carte"
      aria-haspopup="dialog"
      class="size-[52px] min-h-[52px] shrink-0 justify-center p-0"
      :ui="{ leadingIcon: 'size-[22px]' }"
      @click="isMapDrawerOpen = true"
    />
    <UiMapAppDrawer v-model:open="isMapDrawerOpen" :destination="mapDestination" />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterPlaceCardProps } from '~/types/LitterPlaceCard'
import type { MapDestination } from '~/types/Location'
import { computed, ref } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterPlaceCardProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const isMapDrawerOpen: Ref<boolean> = ref(false)

const mapDestination: ComputedRef<MapDestination | null> = computed((): MapDestination | null =>
  LitterDetailPresentation.buildMapDestination(props.litter),
)
const distanceLabel: ComputedRef<string | null> = computed((): string | null =>
  LitterPresentation.buildDistanceLabel(props.litter, locationStore.position),
)
</script>
