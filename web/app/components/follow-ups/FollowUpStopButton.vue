<template>
  <div class="border-t border-line pt-4">
    <button
      v-if="!isConfirmationShown"
      type="button"
      class="min-h-11 border-0 bg-transparent px-1 text-[15px] font-extrabold text-coral-text"
      @click="isConfirmationShown = true"
    >
      {{ props.label }}
    </button>
    <UiInlineConfirmation
      v-else
      :question="props.question"
      :consequence="props.consequence"
      confirm-label="Ne plus suivre"
      :confirm-action="props.stopAction"
      @cancelled="isConfirmationShown = false"
    />
  </div>
</template>

<script lang="ts" setup>
import type { PropType, Ref } from 'vue'
import type { FollowUpStopButtonProps } from '~/types/FollowUpStopButton'
import { ref } from 'vue'

const props: FollowUpStopButtonProps = defineProps({
  label: { type: String, required: true },
  question: { type: String, required: true },
  consequence: { type: String, required: true },
  stopAction: { type: Function as PropType<() => Promise<void>>, required: true },
})

const isConfirmationShown: Ref<boolean> = ref(false)
</script>
