<template>
  <div class="flex items-center gap-2.5 px-1 md:gap-3">
    <div aria-hidden="true" class="grid flex-1 grid-cols-4 gap-[5px] md:gap-1.5">
      <span
        v-for="segment in PASSWORD_STRENGTH_SEGMENT_COUNT"
        :key="segment"
        class="h-[5px] rounded-full md:h-1.5"
        :class="segment <= strength.filledSegmentCount ? strength.segmentClass : 'bg-avatar'"
      />
    </div>
    <span
      aria-live="polite"
      class="min-w-20 text-end text-[13px] font-extrabold md:text-sm"
      :class="strength.labelClass"
    >
      {{ strength.label }}
    </span>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { PasswordStrengthDisplay } from '~/types/PasswordStrength'
import type { UiPasswordStrengthMeterProps } from '~/types/UiPasswordStrengthMeter'
import { computed } from 'vue'
import { PASSWORD_STRENGTH_DISPLAYS, PASSWORD_STRENGTH_SEGMENT_COUNT } from '~/constants/passwordRules'
import { PasswordRules } from '~/utils/passwordRules'

const props: UiPasswordStrengthMeterProps = defineProps({
  password: { type: String, required: true },
})

const strength: ComputedRef<PasswordStrengthDisplay> = computed(
  (): PasswordStrengthDisplay => PASSWORD_STRENGTH_DISPLAYS[PasswordRules.measureStrengthLevel(props.password)],
)
</script>
