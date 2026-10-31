<template>
  <NuxtLink v-slot="{ href, navigate }" :to="`/eleveurs/${props.breeder.id}`" custom>
    <a
      :href="href ?? undefined"
      :aria-current="props.isSelected ? 'true' : undefined"
      class="relative flex flex-col gap-2.5 rounded-card-compact border-2 bg-card p-4 text-ink no-underline shadow-card hover:text-ink"
      :class="props.isSelected ? 'border-coral' : 'border-transparent'"
      @click="activate($event, navigate)"
    >
      <UiCustomIcon
        v-if="props.breeder.is_followed"
        name="heart-filled"
        :size-in-pixels="22"
        class="absolute top-[18px] right-[18px] size-[22px] text-coral"
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
    </a>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { BreederCard } from '~/types/api'
import type { BreederChip, BreederLitterStatusLine } from '~/types/Breeder'
import type { BreederGridCardEmits, BreederGridCardProps } from '~/types/BreederGridCard'
import { computed } from 'vue'
import { BREEDER_LITTER_STATUS_LINE_CLASSES } from '~/constants/breederOptions'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederGridCardProps = defineProps({
  breeder: { type: Object as PropType<BreederCard>, required: true },
  isSelected: { type: Boolean, default: false },
})

const emit: BreederGridCardEmits = defineEmits<{
  (event: 'activate', clickEvent: MouseEvent): void
}>()

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const litterStatusLine: ComputedRef<BreederLitterStatusLine> = computed((): BreederLitterStatusLine =>
  BreederPresentation.buildLitterStatusLine(props.breeder, new Date()),
)
const chips: ComputedRef<BreederChip[]> = computed((): BreederChip[] =>
  BreederPresentation.listChips(props.breeder, true),
)

/**
 * Let the page show the breeder in its side panel, otherwise open its page.
 *
 * @param clickEvent - The click on the card.
 * @param navigate - Navigation of the link, run unless the page took the click.
 */
function activate(clickEvent: MouseEvent, navigate: (event?: MouseEvent) => Promise<unknown>): void {
  emit('activate', clickEvent)
  if (!clickEvent.defaultPrevented) {
    navigate(clickEvent)
  }
}
</script>
