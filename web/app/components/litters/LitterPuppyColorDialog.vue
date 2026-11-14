<template>
  <UiDialog
    :open="props.open"
    :title="dialogTitle"
    :description="dialogDescription"
    has-cream-background
    :drawer-ui="{
      content: 'rounded-t-3xl bg-cream md:mx-auto md:w-full md:max-w-md',
      container: 'gap-4 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body="{ isShownAsWindow }">
      <div v-if="props.puppyLine" class="flex flex-col gap-4">
        <img
          v-if="props.puppyLine.photoUrl"
          :src="props.puppyLine.photoUrl"
          :alt="`Photo du ${props.puppyLine.label.toLowerCase()}`"
          class="h-[220px] w-full rounded-[20px] object-cover object-[center_40%] md:h-[250px]"
        />
        <div class="flex flex-col gap-1.5">
          <span class="text-[11px] font-extrabold text-ink-label uppercase md:text-[13px]">Couleur</span>
          <ul class="m-0 flex list-none flex-col gap-2.5 p-0" aria-label="Couleurs possibles">
            <li v-for="row in offeredColorRows" :key="row.color">
              <CoatColorCheckButton
                :color="row.color"
                :is-checked="colorDraft === row.color"
                :is-disabled="isSaving"
                is-bordered
                @click="chooseColor(row.color)"
              />
            </li>
          </ul>
          <button
            v-if="canOfferEveryColor"
            type="button"
            :disabled="isSaving"
            class="min-h-9 self-start border-0 bg-transparent p-0 text-sm font-extrabold text-coral-text disabled:opacity-60"
            @click="isEveryColorOffered = true"
          >
            Voir les autres couleurs
          </button>
        </div>
        <div :class="isShownAsWindow ? 'grid grid-cols-2 items-center gap-2.5' : 'flex flex-col gap-2.5'">
          <UButton
            size="xl"
            class="min-h-[56px] w-full justify-center text-[17px]"
            :class="isShownAsWindow ? 'order-last' : ''"
            :loading="isSaving"
            @click="saveColor"
          >
            Enregistrer
          </UButton>
          <UButton
            color="neutral"
            variant="outline"
            size="xl"
            class="min-h-[52px] w-full justify-center text-[17px]"
            :disabled="isSaving"
            @click="emit('update:open', false)"
          >
            Annuler
          </UButton>
        </div>
      </div>
    </template>
  </UiDialog>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { CoatColor, LitterColor, LitterDetail, LitterExpectedColor } from '~/types/api'
import type { CriteriaColorRow } from '~/types/Criteria'
import type { LitterPuppyLine } from '~/types/Litter'
import type { LitterPuppyColorDialogEmits, LitterPuppyColorDialogProps } from '~/types/LitterPuppyColorDialog'
import { computed, ref, watch } from 'vue'
import { ALL_COLOR_ROWS } from '~/constants/criteriaOptions'

const props: LitterPuppyColorDialogProps = defineProps({
  open: { type: Boolean, required: true },
  litter: { type: Object as PropType<LitterDetail>, required: true },
  puppyLine: { type: Object as PropType<LitterPuppyLine | null>, default: null },
})
const emit: LitterPuppyColorDialogEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
const toast: ReturnType<typeof useToast> = useToast()

const colorDraft: Ref<CoatColor | null> = ref(null)
const isEveryColorOffered: Ref<boolean> = ref(false)
const isSaving: Ref<boolean> = ref(false)

const dialogTitle: ComputedRef<string> = computed((): string => {
  const puppyLine: LitterPuppyLine | null = props.puppyLine
  if (puppyLine === null) {
    return 'Le chiot'
  }
  return puppyLine.sexLabel ? `${puppyLine.label} · ${puppyLine.sexLabel}` : puppyLine.label
})
const dialogDescription: ComputedRef<string> = computed((): string => {
  const question: string = 'Quelle couleur ? Sa photo aide, l’éleveur confirme.'
  const stateLabel: string | null = props.puppyLine?.stateLabel ?? null
  return stateLabel === null ? question : `${stateLabel}. ${question}`
})
const litterColors: ComputedRef<CoatColor[]> = computed((): CoatColor[] => {
  const colors: CoatColor[] = [
    ...props.litter.colors.map((reading: LitterColor): CoatColor => reading.color),
    ...(props.litter.expected_colors ?? []).map((expected: LitterExpectedColor): CoatColor => expected.color),
  ]
  return [...new Set(colors)].filter((color: CoatColor): boolean => color !== 'inconnue')
})
const canOfferEveryColor: ComputedRef<boolean> = computed(
  (): boolean => !isEveryColorOffered.value && litterColors.value.length > 0,
)
const offeredColorRows: ComputedRef<CriteriaColorRow[]> = computed((): CriteriaColorRow[] =>
  canOfferEveryColor.value
    ? ALL_COLOR_ROWS.filter(
        (row: CriteriaColorRow): boolean => litterColors.value.includes(row.color) || row.color === colorDraft.value,
      )
    : ALL_COLOR_ROWS,
)

/**
 * Tick a colour, or untick the one ticked to go back to what the ad says.
 *
 * @param color - The colour tapped.
 */
function chooseColor(color: CoatColor): void {
  colorDraft.value = colorDraft.value === color ? null : color
}

/**
 * Send the ticked colour, close the window, and say why when the API refuses.
 */
async function saveColor(): Promise<void> {
  if (props.puppyLine === null) {
    return
  }
  isSaving.value = true
  try {
    await littersStore.confirmPuppyColor(props.litter.id, props.puppyLine.listingId, colorDraft.value)
    emit('update:open', false)
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Couleur non enregistrée', color: 'error' })
  } finally {
    isSaving.value = false
  }
}

watch(
  (): [boolean, number | null] => [props.open, props.puppyLine?.listingId ?? null],
  (): void => {
    colorDraft.value = props.puppyLine?.knownColor ?? null
    isEveryColorOffered.value = false
  },
  { immediate: true },
)
</script>
