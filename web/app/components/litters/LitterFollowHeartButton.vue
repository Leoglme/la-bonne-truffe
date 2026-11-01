<template>
  <button
    type="button"
    :aria-label="props.litter.follow_up ? 'Suivie, gérer le suivi' : 'Ajouter au suivi'"
    :aria-haspopup="props.litter.follow_up ? 'dialog' : undefined"
    :aria-busy="isFollowUpActionRunning"
    :disabled="isFollowUpActionRunning"
    class="inline-flex size-11 items-center justify-center rounded-full bg-card text-coral shadow-floating-over-photo md:size-[52px] md:shadow-floating"
    @click="followOrOpenFollowUp"
  >
    <UIcon v-if="isFollowUpActionRunning" name="i-lucide-loader-circle" class="size-5 animate-spin md:size-[22px]" />
    <UiCustomIcon
      v-else
      :name="props.litter.follow_up ? 'heart-filled' : 'heart'"
      :size-in-pixels="22"
      :stroke-width="2.2"
      class="size-5 md:size-[22px]"
    />
  </button>
</template>

<script lang="ts" setup>
import type { PropType, Ref } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterFollowHeartButtonProps } from '~/types/LitterFollowHeartButton'
import { ref } from 'vue'

const props: LitterFollowHeartButtonProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const toast: ReturnType<typeof useToast> = useToast()
const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()

const isFollowUpActionRunning: Ref<boolean> = ref(false)

/**
 * Follow the litter, or open its follow-up drawer once it is followed.
 */
async function followOrOpenFollowUp(): Promise<void> {
  isFollowUpActionRunning.value = true
  try {
    await littersStore.followOrOpenFollowUp(props.litter)
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Suivi impossible', color: 'error' })
  } finally {
    isFollowUpActionRunning.value = false
  }
}
</script>
