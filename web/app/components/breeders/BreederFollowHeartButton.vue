<template>
  <button
    type="button"
    :aria-label="props.breeder.follow ? 'Éleveur suivi, modifier les alertes' : 'Suivre cet éleveur'"
    aria-haspopup="dialog"
    class="inline-flex size-11 items-center justify-center rounded-full border-0 bg-card text-coral shadow-floating-over-photo md:size-[52px] md:shadow-floating"
    @click="breederFollowStore.openWith(props.breeder)"
  >
    <UiCustomIcon
      :name="props.breeder.follow ? 'heart-filled' : 'heart'"
      :size-in-pixels="22"
      :stroke-width="2.2"
      class="size-5 md:size-[22px]"
    />
  </button>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederFollowHeartButtonProps } from '~/types/BreederFollowHeartButton'

const props: BreederFollowHeartButtonProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
})

const breederFollowStore: ReturnType<typeof useBreederFollowStore> = useBreederFollowStore()
</script>
