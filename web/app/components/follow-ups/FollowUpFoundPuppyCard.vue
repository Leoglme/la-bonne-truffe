<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-3.5 rounded-tile bg-cream p-[18px]">
      <div class="flex items-center gap-3.5">
        <LitterTileFrame :litter="props.litter" class="size-16 shrink-0 overflow-hidden rounded-tile-compact">
          <LitterVisual :litter="props.litter" :illustration-size-in-pixels="46" photo-position="center 30%" />
        </LitterTileFrame>
        <span class="flex flex-col gap-0.5">
          <span class="font-display text-xl leading-[1.15] font-semibold">C’est lui ?</span>
          <span class="text-sm text-ink-muted">
            La recherche se met en pause et l’app t’aide à préparer son arrivée. Tu reprends quand tu veux.
          </span>
        </span>
      </div>
      <div class="flex flex-col gap-2.5">
        <div class="flex items-center justify-between gap-3">
          <label :for="arrivalDayFieldId" class="text-[15px] font-bold">Il arrive le</label>
          <input
            :id="arrivalDayFieldId"
            v-model="arrivalOn"
            type="date"
            class="min-h-11 rounded-xl border-0 bg-chip px-3 text-[15px] font-bold text-ink"
          />
        </div>
        <UButton
          size="lg"
          loading-auto
          :disabled="arrivalOn === ''"
          class="min-h-[52px] w-full justify-center px-3 text-base"
          @click="confirmPuppy"
        >
          C’est lui ! Préparer son arrivée
        </UButton>
      </div>
    </div>
    <button
      type="button"
      class="min-h-11 self-center border-0 bg-transparent px-1 text-[15px] font-extrabold text-ink-secondary"
      @click="emit('dismissed')"
    >
      Réservé, mais je continue à regarder
    </button>
  </div>
</template>

<script lang="ts" setup>
import type { PropType, Ref } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { FollowUpFoundPuppyCardEmits, FollowUpFoundPuppyCardProps } from '~/types/FollowUpFoundPuppyCard'
import { ref, useId } from 'vue'
import { PuppyArrivalPresentation } from '~/utils/puppyArrivalPresentation'

const props: FollowUpFoundPuppyCardProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const emit: FollowUpFoundPuppyCardEmits = defineEmits<{
  (event: 'confirmed' | 'dismissed'): void
}>()

const puppyArrivalStore: ReturnType<typeof usePuppyArrivalStore> = usePuppyArrivalStore()

const arrivalDayFieldId: string = useId()

const arrivalOn: Ref<string> = ref(PuppyArrivalPresentation.suggestArrivalDay(props.litter, new Date()))

/**
 * Pause the search on this puppy, then leave for its arrival screen.
 */
async function confirmPuppy(): Promise<void> {
  await puppyArrivalStore.start(props.litter.id, arrivalOn.value)
  emit('confirmed')
  await navigateTo('/')
}
</script>
