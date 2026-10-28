<template>
  <UInput
    :model-value="props.modelValue"
    :type="isPasswordVisible ? 'text' : 'password'"
    :autocomplete="props.autocomplete"
    size="xl"
    class="w-full"
    @update:model-value="updatePassword"
  >
    <template #trailing>
      <UButton
        color="neutral"
        variant="ghost"
        :icon="isPasswordVisible ? 'i-lucide-eye-off' : 'i-lucide-eye'"
        :aria-label="isPasswordVisible ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
        class="size-11 justify-center rounded-xl text-ink-secondary hover:bg-chip active:bg-chip"
        @click="isPasswordVisible = !isPasswordVisible"
      />
    </template>
  </UInput>
</template>

<script lang="ts" setup>
import type { PropType, Ref } from 'vue'
import type { UiPasswordInputAutocomplete, UiPasswordInputEmits, UiPasswordInputProps } from '~/types/UiPasswordInput'
import { ref } from 'vue'

const props: UiPasswordInputProps = defineProps({
  modelValue: { type: String, required: true },
  autocomplete: { type: String as PropType<UiPasswordInputAutocomplete>, required: true },
})

const emit: UiPasswordInputEmits = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

const isPasswordVisible: Ref<boolean> = ref(false)

/**
 * Pass the typed password up.
 *
 * @param value - Value of the field.
 */
function updatePassword(value: string | number): void {
  emit('update:modelValue', String(value))
}
</script>
