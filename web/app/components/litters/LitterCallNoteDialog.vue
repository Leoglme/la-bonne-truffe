<template>
  <UiDialog
    :open="props.open"
    title="Après ton appel"
    description="Note ce que l’éleveur t’a dit : la fiche et la liste afficheront la bonne couleur."
    has-cream-background
    :drawer-ui="{
      content: 'rounded-t-3xl bg-cream md:mx-auto md:w-full md:max-w-md',
      container: 'gap-4 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <LitterCallConfirmation :litter="props.litter" is-in-window @closed="emit('update:open', false)" />
    </template>
  </UiDialog>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterCallNoteDialogEmits, LitterCallNoteDialogProps } from '~/types/LitterCallNoteDialog'

const props: LitterCallNoteDialogProps = defineProps({
  open: { type: Boolean, required: true },
  litter: { type: Object as PropType<LitterDetail>, required: true },
})
const emit: LitterCallNoteDialogEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()
</script>
