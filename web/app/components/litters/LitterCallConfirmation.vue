<template>
  <section
    v-if="canConfirmColor || canConfirmSexes"
    aria-label="À confirmer après ton appel"
    class="flex flex-col"
    :class="
      props.isInWindow
        ? 'gap-5'
        : 'gap-3 rounded-[20px] bg-card px-4 py-3.5 shadow-card md:gap-4 md:rounded-card-compact md:px-[22px] md:py-5'
    "
  >
    <h2 v-if="!props.isInWindow" class="m-0 font-display text-[17px] font-semibold md:text-xl">Après ton appel</h2>

    <div v-if="canConfirmColor" class="flex flex-col gap-1.5">
      <span class="text-[11px] font-extrabold text-ink-label uppercase md:text-[13px]">Couleur</span>
      <template v-if="confirmedColors.length > 0 && !isColorChooserOpen && !props.isInWindow">
        <ul class="m-0 flex list-none flex-col p-0">
          <li
            v-for="row in confirmedColorRows"
            :key="row.color"
            class="flex min-h-12 items-center gap-3 text-[15px] font-bold md:text-[17px]"
          >
            <CockerIllustration :coat="row.coat" :size-in-pixels="40" />
            {{ COAT_COLOR_LABELS[row.color] }}
          </li>
        </ul>
        <div class="flex gap-5">
          <button
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-coral-text disabled:opacity-60"
            @click="openColorChooser"
          >
            Changer
          </button>
          <button
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-ink-muted disabled:opacity-60"
            @click="sendConfirmedColors([])"
          >
            Retirer
          </button>
        </div>
      </template>
      <template v-else>
        <ul
          class="m-0 list-none p-0"
          :class="isColorGridShown ? 'grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-2.5' : 'flex flex-col'"
          aria-label="Couleurs possibles"
        >
          <li
            v-for="row in offeredColorRows"
            :key="row.color"
            :class="isColorGridShown ? '' : 'border-t border-line first:border-t-0'"
          >
            <CoatColorCheckButton
              :color="row.color"
              :is-checked="isColorChecked(row.color)"
              :is-disabled="isSaving"
              :is-bordered="isColorGridShown"
              @click="toggleColor(row.color)"
            />
          </li>
        </ul>
        <div class="flex flex-wrap gap-x-5 gap-y-1">
          <button
            v-if="canOfferEveryColor"
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-coral-text disabled:opacity-60"
            @click="isEveryColorOffered = true"
          >
            Voir les autres couleurs
          </button>
          <button
            v-if="confirmedColors.length > 0 && !props.isInWindow"
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-ink-muted disabled:opacity-60"
            @click="isColorChooserOpen = false"
          >
            Fermer
          </button>
        </div>
      </template>
    </div>

    <div v-if="canConfirmSexes" class="flex flex-col gap-2">
      <span class="text-[11px] font-extrabold text-ink-label uppercase md:text-[13px]">Chiots</span>
      <template v-if="props.litter.has_confirmed_sexes && !isSexEditorOpen && !props.isInWindow">
        <p class="m-0 flex items-center gap-1.5 text-sm text-ink-secondary md:text-base">
          Confirmés après ton appel :
          <LitterSexCounts :litter="props.litter" class="font-bold text-ink" />
        </p>
        <div class="flex gap-5">
          <button
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-coral-text disabled:opacity-60"
            @click="openSexEditor"
          >
            Changer
          </button>
          <button
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-ink-muted disabled:opacity-60"
            @click="sendConfirmedSexes(null, null)"
          >
            Retirer
          </button>
        </div>
      </template>
      <template v-else>
        <UiCountStepper v-model="maleCountDraft" label="Mâles" :maximum="MAX_PUPPIES_PER_SEX">
          <template #label>
            <span class="inline-flex items-center gap-1.5">
              <UIcon name="i-lucide-mars" class="size-5 text-male" aria-hidden="true" />
              Mâles
            </span>
          </template>
        </UiCountStepper>
        <UiCountStepper v-model="femaleCountDraft" label="Femelles" :maximum="MAX_PUPPIES_PER_SEX">
          <template #label>
            <span class="inline-flex items-center gap-1.5">
              <UIcon name="i-lucide-venus" class="size-5 text-female" aria-hidden="true" />
              Femelles
            </span>
          </template>
        </UiCountStepper>
        <div v-if="!props.isInWindow" class="mt-1 flex flex-wrap items-center gap-x-5 gap-y-1">
          <UButton
            size="lg"
            :disabled="!hasSexDraftChanged"
            :loading="isSaving"
            @click="sendConfirmedSexes(maleCountDraft, femaleCountDraft)"
          >
            Enregistrer les chiots
          </UButton>
          <button
            v-if="isSexEditorOpen"
            type="button"
            :disabled="isSaving"
            class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-ink-muted disabled:opacity-60"
            @click="isSexEditorOpen = false"
          >
            Annuler
          </button>
        </div>
      </template>
    </div>

    <div v-if="props.isInWindow" class="grid grid-cols-2 items-center gap-2.5">
      <UButton
        color="neutral"
        variant="outline"
        size="xl"
        class="min-h-[52px] w-full justify-center text-[17px]"
        :disabled="isSaving"
        @click="emit('closed')"
      >
        Annuler
      </UButton>
      <UButton
        size="xl"
        class="min-h-[56px] w-full justify-center text-[17px]"
        :loading="isSaving"
        @click="saveWindowChoices"
      >
        Enregistrer
      </UButton>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { CoatColor, LitterColor, LitterDetail, LitterSourceListing } from '~/types/api'
import type { CriteriaColorRow } from '~/types/Criteria'
import type { LitterCallConfirmationEmits, LitterCallConfirmationProps } from '~/types/LitterCallConfirmation'
import { computed, ref, watch } from 'vue'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { ALL_COLOR_ROWS } from '~/constants/criteriaOptions'
import { MAX_PUPPIES_PER_SEX } from '~/constants/litterLimits'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterCallConfirmationProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInWideLayout: { type: Boolean, default: false },
  isInWindow: { type: Boolean, default: false },
})
const emit: LitterCallConfirmationEmits = defineEmits<{
  (event: 'closed'): void
}>()

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
const toast: ReturnType<typeof useToast> = useToast()

const isColorChooserOpen: Ref<boolean> = ref(false)
const isEveryColorOffered: Ref<boolean> = ref(false)
const isSexEditorOpen: Ref<boolean> = ref(false)
const isSaving: Ref<boolean> = ref(false)
const maleCountDraft: Ref<number> = ref(0)
const femaleCountDraft: Ref<number> = ref(0)
const colorsDraft: Ref<CoatColor[]> = ref([])

const confirmedColors: ComputedRef<CoatColor[]> = computed((): CoatColor[] =>
  props.litter.colors
    .filter((reading: LitterColor): boolean => reading.confidence === 'confirmed')
    .map((reading: LitterColor): CoatColor => reading.color),
)
const canConfirmColor: ComputedRef<boolean> = computed((): boolean => LitterPresentation.canConfirmColor(props.litter))
const isColorGridShown: ComputedRef<boolean> = computed((): boolean => props.isInWideLayout || props.isInWindow)
const hasColorDraftChanged: ComputedRef<boolean> = computed(
  (): boolean =>
    colorsDraft.value.length !== confirmedColors.value.length ||
    colorsDraft.value.some((color: CoatColor): boolean => !confirmedColors.value.includes(color)),
)
const ambiguousColors: ComputedRef<CoatColor[]> = computed((): CoatColor[] => {
  const colors: CoatColor[] = props.litter.listings
    .filter((listing: LitterSourceListing): boolean => listing.is_active)
    .flatMap((listing: LitterSourceListing): LitterColor[] => listing.colors)
    .filter((reading: LitterColor): boolean => reading.confidence === 'ambiguous' && reading.color !== 'inconnue')
    .map((reading: LitterColor): CoatColor => reading.color)
  return [...new Set(colors)]
})
const canOfferEveryColor: ComputedRef<boolean> = computed(
  (): boolean => !isEveryColorOffered.value && ambiguousColors.value.length > 0,
)
const offeredColorRows: ComputedRef<CriteriaColorRow[]> = computed((): CriteriaColorRow[] =>
  canOfferEveryColor.value
    ? ALL_COLOR_ROWS.filter((row: CriteriaColorRow): boolean => ambiguousColors.value.includes(row.color))
    : ALL_COLOR_ROWS,
)
const confirmedColorRows: ComputedRef<CriteriaColorRow[]> = computed((): CriteriaColorRow[] =>
  ALL_COLOR_ROWS.filter((row: CriteriaColorRow): boolean => confirmedColors.value.includes(row.color)),
)
const canConfirmSexes: ComputedRef<boolean> = computed((): boolean => LitterPresentation.canConfirmSexes(props.litter))
const hasSexDraftChanged: ComputedRef<boolean> = computed(
  (): boolean =>
    maleCountDraft.value !== (props.litter.male_count ?? 0) ||
    femaleCountDraft.value !== (props.litter.female_count ?? 0),
)

/**
 * Whether a colour is among the confirmed ones.
 *
 * @param color - Canonical colour.
 * @returns True when confirmed.
 */
function isColorConfirmed(color: CoatColor): boolean {
  return confirmedColors.value.includes(color)
}

/**
 * Whether a colour row shows ticked: the confirmed colours, or in the window the colours chosen before saving.
 *
 * @param color - Canonical colour.
 * @returns True when ticked.
 */
function isColorChecked(color: CoatColor): boolean {
  return props.isInWindow ? colorsDraft.value.includes(color) : isColorConfirmed(color)
}

/**
 * Show the colour rows, those of the source bundle first.
 */
function openColorChooser(): void {
  isEveryColorOffered.value = false
  isColorChooserOpen.value = true
}

/**
 * Add a colour to the confirmed ones, or take it out; the litter is re-scored at once.
 *
 * @param color - The colour tapped.
 */
async function toggleColor(color: CoatColor): Promise<void> {
  if (props.isInWindow) {
    colorsDraft.value = colorsDraft.value.includes(color)
      ? colorsDraft.value.filter((chosen: CoatColor): boolean => chosen !== color)
      : [...colorsDraft.value, color]
    return
  }
  const colors: CoatColor[] = isColorConfirmed(color)
    ? confirmedColors.value.filter((confirmed: CoatColor): boolean => confirmed !== color)
    : [...confirmedColors.value, color]
  await sendConfirmedColors(colors)
}

/**
 * Send the confirmed colours to the API, and say why when it refuses.
 *
 * @param colors - The confirmed colours, none to go back to what the sources say.
 */
async function sendConfirmedColors(colors: CoatColor[]): Promise<void> {
  isSaving.value = true
  try {
    await littersStore.confirmColors(props.litter.id, colors)
    if (colors.length === 0) {
      openColorChooser()
    }
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Couleur non enregistrée', color: 'error' })
  } finally {
    isSaving.value = false
  }
}

/**
 * Show the counters, set to the sexes known so far.
 */
function openSexEditor(): void {
  resetSexDrafts()
  isSexEditorOpen.value = true
}

/**
 * Set the counters to the sexes the litter shows, or to zero while unknown.
 */
function resetSexDrafts(): void {
  maleCountDraft.value = props.litter.male_count ?? 0
  femaleCountDraft.value = props.litter.female_count ?? 0
}

/**
 * Send the confirmed sexes to the API, and say why when it refuses.
 *
 * @param maleCount - Males heard from the breeder, null with the females to go back to what the sources say.
 * @param femaleCount - Females heard from the breeder.
 */
async function sendConfirmedSexes(maleCount: number | null, femaleCount: number | null): Promise<void> {
  isSaving.value = true
  try {
    await littersStore.confirmSexes(props.litter.id, maleCount, femaleCount)
    isSexEditorOpen.value = false
    resetSexDrafts()
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Chiots non enregistrés', color: 'error' })
  } finally {
    isSaving.value = false
  }
}

/**
 * Send what the window holds, the colours then the sexes that changed, and close it; say why when the API refuses.
 */
async function saveWindowChoices(): Promise<void> {
  isSaving.value = true
  try {
    if (canConfirmColor.value && hasColorDraftChanged.value) {
      await littersStore.confirmColors(props.litter.id, colorsDraft.value)
    }
    if (canConfirmSexes.value && hasSexDraftChanged.value) {
      await littersStore.confirmSexes(props.litter.id, maleCountDraft.value, femaleCountDraft.value)
    }
    emit('closed')
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Non enregistré', color: 'error' })
  } finally {
    isSaving.value = false
  }
}

watch(
  (): number => props.litter.id,
  (): void => {
    colorsDraft.value = [...confirmedColors.value]
    isColorChooserOpen.value = confirmedColors.value.length === 0
    isEveryColorOffered.value = false
    isSexEditorOpen.value = false
    resetSexDrafts()
  },
  { immediate: true },
)
</script>
